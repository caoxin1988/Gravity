---
layout: post
title:  "Looper和Handler类"
subtitle: dacaoxin
author: dacaoxin
date:   2016-11-27 17:00:00
catalog:  true
tags:
    - android
    - framework
    - java
    - handler
---

## Looper  
Looper是用来封装消息循环，并且为线程提供一个消息队列。android中的线程默认是没有消息循环机制的，可以在线程中使用Looper.prepare()创建一个消息循环，并使用Looper.loop()让它可以处理消息。下面是一个例程:

    class LooperThread extends Thread {
        public Handler mHandler;

        public void run() {
        Looper.prepare();

        mHandler = new Handler() {
            public void handleMessage(Message msg) {
                // process incoming messages here
            }
        };

          Looper.loop();
        }
    }

* 所谓的准备工作  
[-> framework/base/core/java/android/os/Looper.java]  


    public static void prepare() {
        prepare(true);
    }

[-> framework/base/core/java/android/os/Looper.java]  

    private static void prepare(boolean quitAllowed) {
        if (sThreadLocal.get() != null) {
            throw new RuntimeException("Only one Looper may be created per thread");
        }
        sThreadLocal.set(new Looper(quitAllowed));
    }

prepare其实就是把Looper对象用一个变量存起来，sThreadLocal是一个ThreadLocal<T>的类对象，它的作用就是为每个使用这个变量的线程提供不同的的副本。

* loop循环  
[-> framework/base/core/java/android/os/Looper.java]    


    public static void loop() {
        final Looper me = myLooper();
        final MessageQueue queue = me.mQueue;
        for (;;) {
            Message msg = queue.next(); // might block
            // msg.target一般指向使用这个looper的handler,即调用Handler.dispatchMessage()处理消息
            msg.target.dispatchMessage(msg);
            msg.recycleUnchecked();
        }
    }

[-> framework/base/core/java/android/os/Looper.java]

    public static Looper myLooper() {
        return sThreadLocal.get();
    }

所以loop()的作用就是从looper的消息队列中循环的取消息，然后让使用这个looper的handler的dispatchMessage()来处理消息。

## ThreadLocal
在使用ThreadLocal维护变量时，ThreadLocal为每个使用该变量的线程提供独立的变量副本，所以每一个线程都可以独立地改变自己的副本，而不会影响其它线程所对应的副本。ThreadLocal类维护着一个类似于map一样的东西，它以每个线程对象自身的hash值作为key, 存着这个线程需要的值。

[-> libcore/luni/src/main/java/java/lang/ThreadLocal.java]

    public void set(T value) {
        Thread currentThread = Thread.currentThread();
        Values values = values(currentThread);
        if (values == null) {
            values = initializeValues(currentThread);
        }
        values.put(this, value);
    }
    
通过Thread.currentThread()可以获取当前所在线程的线程对象currentThread，再查找当前所在线程中保存的Values对象。

[-> libcore/luni/src/main/java/java/lang/ThreadLocal.java]

    Values values(Thread current) {
        return current.localValues;
    }

如果当前所在线程并没有Values对象，创建一个新的。

[-> libcore/luni/src/main/java/java/lang/ThreadLocal.java]

    Values initializeValues(Thread current) {
        return current.localValues = new Values();
    }
    
[-> libcore/luni/src/main/java/java/lang/ThreadLocal.java]

    Values() {
        initializeTable(INITIAL_SIZE);
        this.size = 0;
        this.tombstones = 0;
    }

最后以当前所在线程的hash key作为索引，保存所需要的数据。

[-> libcore/luni/src/main/java/java/lang/ThreadLocal.java]

    void put(ThreadLocal<?> key, Object value) {
        cleanUp();

        // Keep track of first tombstone. That's where we want to go back
        // and add an entry if necessary.
        int firstTombstone = -1;

        for (int index = key.hash & mask;; index = next(index)) {
            Object k = table[index];

            if (k == key.reference) {
                // Replace existing entry.
                table[index + 1] = value;
                return;
            }

            if (k == null) {
                if (firstTombstone == -1) {
                    // Fill in null slot.
                    table[index] = key.reference;
                    table[index + 1] = value;
                    size++;
                    return;
                }

                // Go back and replace first tombstone.
                table[firstTombstone] = key.reference;
                table[firstTombstone + 1] = value;
                tombstones--;
                size++;
                return;
            }

            // Remember first tombstone.
            if (firstTombstone == -1 && k == TOMBSTONE) {
                firstTombstone = index;
            }
        }
    }

最后来看看最像码农一样的民工，Handler

## Handler

* 构造函数  
Handler.java代码里有好几个构造函数，其实最终调用的都是下面两个中的一个:   

[-> frameworks/base/core/java/android/os/Handler.java]

    public Handler(Callback callback, boolean async) {
        if (FIND_POTENTIAL_LEAKS) {
            final Class<? extends Handler> klass = getClass();
            if ((klass.isAnonymousClass() || klass.isMemberClass() || klass.isLocalClass()) &&
                    (klass.getModifiers() & Modifier.STATIC) == 0) {
                Log.w(TAG, "The following Handler class should be static or leaks might occur: " +
                    klass.getCanonicalName());
            }
        }

        mLooper = Looper.myLooper();
        if (mLooper == null) {
            throw new RuntimeException(
                "Can't create handler inside thread that has not called Looper.prepare()");
        }
        mQueue = mLooper.mQueue;
        mCallback = callback;
        mAsynchronous = async;
    }

[-> frameworks/base/core/java/android/os/Handler.java]

    public Handler(Looper looper, Callback callback, boolean async) {
        mLooper = looper;
        mQueue = looper.mQueue;
        mCallback = callback;
        mAsynchronous = async;
    }

区别就是一个会使用当前线程绑定的Looper, 而另一个则可以传递另外一个线程的looper供这个handler使用。除此之外，Handler的构造函数会获取其使有的looper的消息队列对象。

* 消息发送  
Handler发送消息函数有以下两种：  
> post()系列
> sendMessage() 系列  
它们的实质都是调用sendMessageAtTime(Message msg, long uptimeMillis)实现的

[-> frameworks/base/core/java/android/os/Handler.java]

    public boolean sendMessageAtTime(Message msg, long uptimeMillis) {
        MessageQueue queue = mQueue;
        if (queue == null) {
            RuntimeException e = new RuntimeException(
                    this + " sendMessageAtTime() called with no mQueue");
            Log.w("Looper", e.getMessage(), e);
            return false;
        }
        return enqueueMessage(queue, msg, uptimeMillis);
    }

[-> frameworks/base/core/java/android/os/Handler.java]

    private boolean enqueueMessage(MessageQueue queue, Message msg, long uptimeMillis) {
        msg.target = this;
        if (mAsynchronous) {
            msg.setAsynchronous(true);
        }
        return queue.enqueueMessage(msg, uptimeMillis);
    }
    
可以看到msg的target就是handler对象本身，这一点很重要，前面在loop循环中，就是调用这个函数来处理消息。发送的消息，最终会进入这个handler所使用的looper的消息队列中循环。

* 消息处理  

在loop循环中，不停的调用msg.target.dispatchMessage(msg)来处理消息

[-> frameworks/base/core/java/android/os/Handler.java]

    public void dispatchMessage(Message msg) {
        if (msg.callback != null) {
            handleCallback(msg);
        } else {
            if (mCallback != null) {
                if (mCallback.handleMessage(msg)) {
                    return;
                }
            }
            handleMessage(msg);
        }
    }
    
如果message自带有callback(), 就调用message的callback()函数处理消息; 如果message没带，而handler带有callback()函数，则调用handler带的callback()函数处理消息; 如果以上都不存在，则最终调用Handler的子类复写的handleMessage()函数处理消息。

# HandlerThread.java  
HandlerThread是Thread的子类，所以实际上，它本质上还是一个线程，只不过这个线程里自带了一个looper, 它可以被用来创建handler。

[-> frameworks/base/core/java/android/os/HandlerThread.java]

    public void run() {
        mTid = Process.myTid();
        Looper.prepare();
        synchronized (this) {
            mLooper = Looper.myLooper();
            notifyAll();
        }
        Process.setThreadPriority(mPriority);
        onLooperPrepared();
        Looper.loop();
        mTid = -1;
    }
    
