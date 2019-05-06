---
layout: post
title:  "Android native线程分析"
subtitle: dacaoxin
author: dacaoxin
date:   2016-11-10 20:12:50
catalog:  true
tags:
    - android
    - thread
    - native
---

这篇文章主要是为了记录一下android cppn层的线程创建和运行的原理。

代码位置：  
---
> system/core/libutils/Threads.cpp  
> system/core/include/Thread.h  
> system/core/include/utils/Mutex.h  

## 创建本地线程示例  
[->thread_test.h]

    #include <stdint.h>
    #include <utils/Thread.h>
    
    namespace android {
    
    class ThreadTest : public Thread {
    public:
    	ThreadTest();
    	virtual ~ThreadTest();
    
    private:
    	virtual bool threadLoop();
    };
    
    }

[->thread_test.cpp]

    #define LOG_TAG "threadtest"

    #include "thread_test.h"
    #include <utils/Log.h>
    
    namespace android {
    
    ThreadTest::ThreadTest() : Thread(false) {
    	
    }
    
    ThreadTest::~ThreadTest() {
    
    }
    
    bool ThreadTest::threadLoop() {
    	ALOGE("test in threadLoop()");
    	return true;
    }
    
    }

[->threadtest_main.cpp]

    #include <utils/Thread.h>
    #include "thread_test.h"

    using namespace android;

    int main() {
    	sp<ThreadTest> thread = new ThreadTest();
    
    	thread->run();
    
    	while(1);
    
    	return 0;
    }


## 线程函数   
我们先来看看Thread类的构造函数  

    Thread::Thread(bool canCallJava)
    :   mCanCallJava(canCallJava),
        mThread(thread_id_t(-1)),
        mLock("Thread::mLock"),
        mStatus(NO_ERROR),
        mExitPending(false), mRunning(false)
    #ifdef HAVE_ANDROID_OS
            , mTid(-1)
    #endif
    {
    }

上面的例子中，ThreadTest类的构造函数给父类Thread传递的参数是false, mCanCallJava = false,  

    status_t Thread::run(const char* name, int32_t priority, size_t stack) {
        if (mCanCallJava) {
        res = createThreadEtc(_threadLoop,
                this, name, priority, stack, &mThread);
        } else {
            res = androidCreateRawThreadEtc(_threadLoop,
                    this, name, priority, stack, &mThread);
        }
    }
    
run()函数是根据mCanCallJava变量的不同，调用不同的函数开始线程。接着来看看createThreadEtc()和androidCreateRawThreadEtc()，有多大的区别：

    inline bool createThreadEtc(thread_func_t entryFunction,
                            void *userData,
                            const char* threadName = "android:unnamed_thread",
                            int32_t threadPriority = PRIORITY_DEFAULT,
                            size_t threadStackSize = 0,
                            thread_id_t *threadId = 0)
    {
        return androidCreateThreadEtc(entryFunction, userData, threadName,
            threadPriority, threadStackSize, threadId) ? true : false;
    }
    
    int androidCreateThreadEtc(android_thread_func_t entryFunction,
                            void *userData,
                            const char* threadName,
                            int32_t threadPriority,
                            size_t threadStackSize,
                            android_thread_id_t *threadId)
    {
        return gCreateThreadFn(entryFunction, userData, threadName,
            threadPriority, threadStackSize, threadId);
    }
    
gCreateThreadFn又是什么呢？

    static android_create_thread_fn gCreateThreadFn = androidCreateRawThreadEtc;
    
有没有发现，默认的gCreateThreadFn函数指针所指向的函数就是androidCreateRawThreadEtc(), 也就是说，如果当前线程的gCreateThreadFn值没有更改过，mCanCallJava为true和false的时候，产生的效果就是完全一样的。那gCreateThreadFn指向的函数何时会改变呢。

    void androidSetCreateThreadFunc(android_create_thread_fn func)
    {
        gCreateThreadFn = func;
    }
    
那androidSetCreateThreadFunc这个函数怎么用呢？搜索这个函数，可以发现:

[->AndroidRuntime.cpp]

    /*static*/ 
    int AndroidRuntime::startReg(JNIEnv* env)
    {
        /*
         * This hook causes all future threads created in this process to be
         * attached to the JavaVM.  (This needs to go away in favor of JNI
         * Attach calls.)
         */
        androidSetCreateThreadFunc((android_create_thread_fn) javaCreateThreadEtc);
    
        ALOGV("--- registering native functions ---\n");
    
        /*
         * Every "register" function calls one or more things that return
         * a local reference (e.g. FindClass).  Because we haven't really
         * started the VM yet, they're all getting stored in the base frame
         * and never released.  Use Push/Pop to manage the storage.
         */
        env->PushLocalFrame(200);
    
        if (register_jni_procs(gRegJNI, NELEM(gRegJNI), env) < 0) {
            env->PopLocalFrame(NULL);
            return -1;
        }
        env->PopLocalFrame(NULL);
    
        //createJavaThread("fubar", quickTest, (void*) "hello");
    
        return 0;
    }


    int AndroidRuntime::javaCreateThreadEtc(
                                android_thread_func_t entryFunction,
                                void* userData,
                                const char* threadName,
                                int32_t threadPriority,
                                size_t threadStackSize,
                                android_thread_id_t* threadId)
    {
        void** args = (void**) malloc(3 * sizeof(void*));   // javaThreadShell must free
        int result;
    
        if (!threadName)
            threadName = "unnamed thread";
    
        args[0] = (void*) entryFunction;
        args[1] = userData;
        args[2] = (void*) strdup(threadName);   // javaThreadShell must free
    
        result = androidCreateRawThreadEtc(AndroidRuntime::javaThreadShell, args,
            threadName, threadPriority, threadStackSize, threadId);
        return result;
    }


    int AndroidRuntime::javaThreadShell(void* args) {
        void* start = ((void**)args)[0];
        void* userData = ((void **)args)[1];
        char* name = (char*) ((void **)args)[2];        // we own this storage
        free(args);
        JNIEnv* env;
        int result;
    
        /* hook us into the VM */
        if (javaAttachThread(name, &env) != JNI_OK)
            return -1;
    
        /* start the thread running */
        result = (*(android_thread_func_t)start)(userData);
    
        /* unhook us */
        javaDetachThread();
        free(name);
    
        return result;
    }

注意javaAttachThread()，调用了这个函数之后，就会将当前线程和java虚拟机绑定，这样这个线程便有了能力来调用JNI函数。

> 所以cancalljava变量的作用就是区分当前线程可不可以调用JNI函数

## 线程开始运行
在例程中，当调用thread->run()之后，线程运行函数是哪一个呢? 这里以cancalljava = false为例:

    int androidCreateRawThreadEtc(android_thread_func_t fn,
                               void *userData,
                               const char* /*threadName*/,
                               int32_t /*threadPriority*/,
                               size_t /*threadStackSize*/,
                               android_thread_id_t *threadId)
    {
        pthread_attr_t attr; 
        pthread_attr_init(&attr);
        pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
        
        errno = 0;
        pthread_t thread;
        int result = pthread_create(&thread, &attr,
                        (android_pthread_entry)entryFunction, userData);
                        
        if (threadId != NULL) {
        *threadId = (android_thread_id_t)thread; // XXX: this is not portable
        }
        return 1;
    }


其实线程函数就是thread->_threadLoop(this)。

    int Thread::_threadLoop(void* user) {
        Thread* const self = static_cast<Thread*>(user);
        
        bool first = true;
        do {
            bool result;
            if (first) {
                first = false;
                self->mStatus = self->readyToRun();
                result = (self->mStatus == NO_ERROR);
    
                if (result && !self->exitPending()) {
                    // Binder threads (and maybe others) rely on threadLoop
                    // running at least once after a successful ::readyToRun()
                    // (unless, of course, the thread has already been asked to exit
                    // at that point).
                    // This is because threads are essentially used like this:
                    //   (new ThreadSubclass())->run();
                    // The caller therefore does not retain a strong reference to
                    // the thread and the thread would simply disappear after the
                    // successful ::readyToRun() call instead of entering the
                    // threadLoop at least once.
                    result = self->threadLoop();
                }
            } else {
                result = self->threadLoop();
            }
    
            // establish a scope for mLock
            {
            Mutex::Autolock _l(self->mLock);
            if (result == false || self->mExitPending) {
                self->mExitPending = true;
                self->mRunning = false;
                // clear thread ID so that requestExitAndWait() does not exit if
                // called by a new thread using the same thread ID as this one.
                self->mThread = thread_id_t(-1);
                // note that interested observers blocked in requestExitAndWait are
                // awoken by broadcast, but blocked on mLock until break exits scope
                self->mThreadExitedCondition.broadcast();
                break;
            }
            }
            
            // Release our strong reference, to let a chance to the thread
            // to die a peaceful death.
            strong.clear();
            // And immediately, re-acquire a strong reference for the next loop
            strong = weak.promote();
        } while(strong != 0);
    
        return 0;
    }

这里可以得到两个结论  
* 第一次启动线程函数时，会先调用readyToRun(), 然后再调用threadLoop()。非首次启动线程函数，直接调用threadLoop()。这两个函数都是虚函数，如ThreadTest有重写，调用的就是ThreadTest类对象的函数。  
* 有两种方式可以结束当前线程，一是threadLoop()函数返回值为false, 二是mExitPending的值变为true。

## 线程的同步   
涉及到多线程编程，则必然会提到线程之间同步的问题，这里只说一下目前android代码当中使用的最广泛的几种方法：
* AutoLock  
[->system/core/include/utils/Mutex.h]

    class Mutex {
        ...
        class Autolock {
        public:
            inline Autolock(Mutex& mutex) : mLock(mutex)  { mLock.lock(); }
            inline Autolock(Mutex* mutex) : mLock(*mutex) { mLock.lock(); }
            inline ~Autolock() { mLock.unlock(); }
        private:
            Mutex& mLock;
        };
    }

Autolock是Mutex的一个内部类，Autolock的实现可以看出来，它的本质仍然是一个Mutex，它的好处就在于在析构时，系统会自动进行mutex的unlock操作，这样会更加的安全。使用例 子：  
[->frameworks/av/media/libstagefright/AudioPlayer.cpp]

    Mutex mLock;
    bool AudioPlayer::isSeeking() {
        Mutex::Autolock autoLock(mLock);
        return mSeeking;
    }

这样当isSeeking()函数结束时，系统会自动对mLock进行unlock()操作。
