---
layout: post
title:  "Input系统学习之启动"
subtitle: dacaoxin
author: dacaoxin
date:   2017-4-16 16:53:00
catalog:  true
tags:
    - native
    - input
    - android
---

Android的输入系统，这里主要针对按键事件，对于触摸屏，大致流程差不多，后续分析。

## 0 Input系统Native侧类图

右键查看大图

![NativeInputSystem](/images/input/NativeInputSystem.jpg)


## 1 InputManagerService启动

InputManagerService作为系统服务，运行在systemserver进程中。

[frameworks/base/services/java/com/android/server/SystemServer.java]

    private void startOtherServices() {
        InputManagerService inputManager = null;
        
        // 创建一个InputManagerService对象
        inputManager = new InputManagerService(context);
        // 将inputManager作为参数传递给WindowManagerService的成员mInputManager
        wm = WindowManagerService.main(context, inputManager,
                    mFactoryTestMode != FactoryTest.FACTORY_TEST_LOW_LEVEL,
                    !mFirstBoot, mOnlyCore);
        
        ServiceManager.addService(Context.INPUT_SERVICE, inputManager);
        
        // 在inputManager里设置一个WindowManagerService对象的回调对象mWindowManagerCallbacks
        inputManager.setWindowManagerCallbacks(wm.getInputMonitor());
        // 启动native层的reader和dispatcher，开始监听和分发输入事件
        inputManager.start();
    }

## 2 InputManagerService构造函数

[frameworks/base/services/core/java/com/android/server/input/InputManagerService.java]

    public InputManagerService(Context context) {
        this.mContext = context;
        // 启动一个运行在"android.display"线程的handler
        this.mHandler = new InputManagerHandler(DisplayThread.get().getLooper());
        
        mUseDevInputEventForAudioJack =
                context.getResources().getBoolean(R.bool.config_useDevInputEventForAudioJack);
        // 调用native函数初始化, mPtr是指向NativeInputManager对象的指针
        mPtr = nativeInit(this, mContext, mHandler.getLooper().getQueue());
        
        LocalServices.addService(InputManagerInternal.class, new LocalService());
    }

### 2.1 nativeInit

nativeInit是一个JNI函数

[frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp]

    static jlong nativeInit(JNIEnv* env, jclass /* clazz */,
        jobject serviceObj, jobject contextObj, jobject messageQueueObj) {
        // 获取native层的消息队列
        sp<MessageQueue> messageQueue = android_os_MessageQueue_getMessageQueue(env, messageQueueObj);
        if (messageQueue == NULL) {
            jniThrowRuntimeException(env, "MessageQueue is not initialized.");
            return 0;
        }
        // 创建一个NativeInputManager对象
        NativeInputManager* im = new NativeInputManager(contextObj, serviceObj,
                messageQueue->getLooper());
        im->incStrong(0);
        return reinterpret_cast<jlong>(im);
    }

### 2.2 NativeInputManager

[frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp]

    NativeInputManager::NativeInputManager(jobject contextObj,
        jobject serviceObj, const sp<Looper>& looper) :
        mLooper(looper), mInteractive(true) {
        JNIEnv* env = jniEnv();
        
        mContextObj = env->NewGlobalRef(contextObj);
        mServiceObj = env->NewGlobalRef(serviceObj);
        
        {
            AutoMutex _l(mLock);
            mLocked.systemUiVisibility = ASYSTEM_UI_VISIBILITY_STATUS_BAR_VISIBLE;
            mLocked.pointerSpeed = 0;
            mLocked.pointerGesturesEnabled = true;
            mLocked.showTouches = false;
        }
        mInteractive = true;
        // 创建一个EventHub类对象
        sp<EventHub> eventHub = new EventHub();
        // 创建InputManager类对象
        mInputManager = new InputManager(eventHub, this, this);
    }

这里又创建了两个类对象：EventHub和InputManager。

### 2.3 EventHub

[frameworks/native/services/inputflinger/EventHub.cpp]

    EventHub::EventHub(void) :
        mBuiltInKeyboardId(NO_BUILT_IN_KEYBOARD), mNextDeviceId(1), mControllerNumbers(),
        mOpeningDevices(0), mClosingDevices(0),
        mNeedToSendFinishedDeviceScan(false),
        mNeedToReopenDevices(false), mNeedToScanDevices(true),
        mPendingEventCount(0), mPendingEventIndex(0), mPendingINotify(false) {
            // 创建epoll句柄，用于监测
            mEpollFd = epoll_create(EPOLL_SIZE_HINT);
            // 初始化inotify对象
            mINotifyFd = inotify_init();
            // 该inotify监听文件的创建和删除两个事件
            // DEVICE_PATH = /dev/input
            int result = inotify_add_watch(mINotifyFd, DEVICE_PATH, IN_DELETE | IN_CREATE);
        
            struct epoll_event eventItem;
            memset(&eventItem, 0, sizeof(eventItem));
            eventItem.events = EPOLLIN;
            eventItem.data.u32 = EPOLL_ID_INOTIFY;
            // 使用epoll监听mINotifyFd这个句柄的变化
            result = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, mINotifyFd, &eventItem);
        
            int wakeFds[2];
            result = pipe(wakeFds);
        
            mWakeReadPipeFd = wakeFds[0];
            mWakeWritePipeFd = wakeFds[1];
        
            result = fcntl(mWakeReadPipeFd, F_SETFL, O_NONBLOCK);
        
            result = fcntl(mWakeWritePipeFd, F_SETFL, O_NONBLOCK);
        
            eventItem.data.u32 = EPOLL_ID_WAKE;
            // 使用epoll监听mWakeWritePipeFd管道
            result = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, mWakeReadPipeFd, &eventItem);
        }

EventHub的构造函数除了初始化一些变量之外，最重要的工作就是使用inotify和epoll监测'/dev/input'目录下文件的创建与删除, 以及监听读写管道wakeFds[2]。

### 2.4 InputManager

[frameworks/native/services/inputflinger/InputManager.cpp]

    InputManager::InputManager(
        const sp<EventHubInterface>& eventHub,
        const sp<InputReaderPolicyInterface>& readerPolicy,
        const sp<InputDispatcherPolicyInterface>& dispatcherPolicy)
    {
        // 创建InputDispatcher对象，负责按键事件的分发
        mDispatcher = new InputDispatcher(dispatcherPolicy);
        // 创建InputReader对象，负责按键事件的读取和处理
        mReader = new InputReader(eventHub, readerPolicy, mDispatcher);
        initialize();
    }

[frameworks/native/services/inputflinger/InputManager.cpp]

    void InputManager::initialize() {
        // 创建读取和分发按键事件的线程
        mReaderThread = new InputReaderThread(mReader);
        mDispatcherThread = new InputDispatcherThread(mDispatcher);
    }

### 2.5 InputDispatcher

[frameworks/native/services/inputflinger/InputDispatcher.cpp]

    InputDispatcher::InputDispatcher(const sp<InputDispatcherPolicyInterface>& policy) :
        // policy这里就是NativeInputManager类对象
        mPolicy(policy),
        mPendingEvent(NULL), mLastDropReason(DROP_REASON_NOT_DROPPED),
        mAppSwitchSawKeyDown(false), mAppSwitchDueTime(LONG_LONG_MAX),
        mNextUnblockedEvent(NULL),
        mDispatchEnabled(false), mDispatchFrozen(false), mInputFilterEnabled(false),
        mInputTargetWaitCause(INPUT_TARGET_WAIT_CAUSE_NONE)
    {
        mLooper = new Looper(false);
        
        mKeyRepeatState.lastKeyEntry = NULL;
        policy->getDispatcherConfiguration(&mConfig);
    }

### 2.6 InputReader

[frameworks/native/services/inputflinger/InputReader.cpp]

    InputReader::InputReader(const sp<EventHubInterface>& eventHub,
        const sp<InputReaderPolicyInterface>& policy,
        const sp<InputListenerInterface>& listener) :
        mContext(this), mEventHub(eventHub), mPolicy(policy),
        mGlobalMetaState(0), mGeneration(1),
        mDisableVirtualKeysTimeout(LLONG_MIN), mNextTimeout(LLONG_MAX),
        mConfigurationChangesToRefresh(0)
    {
        // listener就是InputManager里创建的InputDispatcher对象
        mQueuedListener = new QueuedInputListener(listener);
        
        {
            AutoMutex _l(mLock);
            
            refreshConfigurationLocked(0);
            updateGlobalMetaStateLocked();
        }
    }
    
mQueuedListener的成员mInnerListener就是InputDispatcher对象，用于后面唤醒dispatcher线程使用。

## 3 inputManager.start

在SystemServr里，通过调用inputManagerService的start()方法开启对按键事件的read和dispatch.

### 3.1 InputManagerService.start()

[frameworks/base/services/core/java/com/android/server/input/InputManagerService.java]

    public void start() {
        // 调用JNI函数nativeStart
        nativeStart(mPtr);
        // 看门狗会监测InputManagerService这个服务
        Watchdog.getInstance().addMonitor(this);
        
        registerPointerSpeedSettingObserver();
        registerShowTouchesSettingObserver();
        
        mContext.registerReceiver(new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                updatePointerSpeedFromSettings();
                updateShowTouchesFromSettings();
            }
        }, new IntentFilter(Intent.ACTION_USER_SWITCHED), null, mHandler);
        // 触摸点显示速度
        updatePointerSpeedFromSettings();
        // 是否显示触摸点
        updateShowTouchesFromSettings();
    }
    
### 3.2 nativeStart()

[frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp]

    static void nativeStart(JNIEnv* env, jclass /* clazz */, jlong ptr) {
        // ptr是NativeInputManager类对象的指针
        NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);
        // 调用NativeInputManager类对象里InputManager对象的start()函数
        status_t result = im->getInputManager()->start();
    }

调用InputManager类的start()函数。

[frameworks/native/services/inputflinger/InputManager.cpp]

    status_t InputManager::start() {
        // 开启InputDispatcher线程
        status_t result = mDispatcherThread->run("InputDispatcher", PRIORITY_URGENT_DISPLAY);
        if (result) {
            ALOGE("Could not start InputDispatcher thread due to error %d.", result);
            return result;
        }
        // 开启InputReader线程
        result = mReaderThread->run("InputReader", PRIORITY_URGENT_DISPLAY);
        if (result) {
            mDispatcherThread->requestExit();
            return result;
        }
        
        return OK;
    }
    
InputDispatcher和InputReader线程开启之后，InputDispatcherThread::threadLoop()和InputReaderThread::threadLoop()开始循环执行,
实际上就是InputDispatcher::dispatchOnce()和InputReader::loopOnce()。

## 4 总结

SystemServer启动InputManagerService服务之后，主要是创建了两个线程InputDispatcher和InputReader，分别用于读取按键以及分发按键给framework。
