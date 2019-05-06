---
layout: post
title:  "MountService分析"
subtitle: dacaoxin
author: dacaoxin
date:   2017-3-22 19:03:00
catalog:  true
tags:
    - framework
    - mountservice
    - android
---

## 1 mountservice架构图

![mountservice类继承关系图](/images/vold/mountservice.jpg)

## 2 MountService和Vold

![mountservice & vold](/images/vold/mountservice_flow.jpg)

## 3 MountService启动

MountService是众多系统服务中的一个，它是运行在SystemServer进程中。

### 3.1 SystemServer进程    

[frameworks/base/services/java/com/android/server/SystemServer.java]

    private void startOtherServices() {
        // MOUNT_SERVICE_CLASS = "com.android.server.MountService$Lifecycle"
        // 实际上就是调用MountService$Lifecycle类的onStart()方法
        mSystemServiceManager.startService(MOUNT_SERVICE_CLASS);
        // 获取Mountservice的Binder代理端
        mountService = IMountService.Stub.asInterface(
                            ServiceManager.getService("mount"));
        ... ...
        
        mActivityManagerService.systemReady(new Runnable() {
            @Override
            public void run() {
                ... ...
                // 通过PHASE_ACTIVITY_MANAGER_READY启动MountService
                mSystemServiceManager.startBootPhase(
                        SystemService.PHASE_ACTIVITY_MANAGER_READY);
                
                ... ...
            }
    }
    
[frameworks/base/services/core/java/com/android/server/MountService.java]

    public static class Lifecycle extends SystemService {
        private MountService mMountService;
        
        public void onStart() {
            // 构造MountService类对象
            mMountService = new MountService(getContext());
            // 将MountService对象添加到systemserver进程中，方便其它进程
            // 可以通过Binder机制调用
            publishBinderService("mount", mMountService);
        }
        
        public void onBootPhase(int phase) {
            // 当使用SystemServiceManager的startBootPhase方法，传入参数为
            // PHASE_ACTIVITY_MANAGER_READY时，调用MountService的systemReady()
            if (phase == SystemService.PHASE_ACTIVITY_MANAGER_READY) {
                mMountService.systemReady();
            }
        }
    }
    
SystemServer里通过MountService的一个内部类Lifecycle来构建MountService的类对象。

### 3.2 MountService

#### 3.2.1 构造函数

[frameworks/base/services/core/java/com/android/server/MountService.java]

    public MountService(Context context) {
        mContext = context;
        
        // mCallbacks继承于Handler类，主要是为了处理IMountServiceListener回调
        mCallbacks = new Callbacks(FgThread.get().getLooper());
        
        HandlerThread hthread = new HandlerThread(TAG);
        hthread.start();
        // MountServiceHandler继承于Handler类，主要为了处理MountService内部的消息
        mHandler = new MountServiceHandler(hthread.getLooper());
        
        // 创建NativeDaemonConnector对象，用于MountService和Vold进程通信
        // MountService将自己的对象注册为NativeDaemonConnector的一个回调
        mConnector = new NativeDaemonConnector(this, "vold", MAX_CONTAINERS * 2, VOLD_TAG, 25,
                null);
        mConnector.setDebug(true);
        
        // 为MountService和vold通信，创建一个新线程
        Thread thread = new Thread(mConnector, VOLD_TAG);
        thread.start();
        
        // 创建内部存储信息
        addInternalVolume();
        
        // 开启这个选项，将MountService列入看门狗监测类中
        if (WATCHDOG_ENABLE) {
            Watchdog.getInstance().addMonitor(this);
        }
    }
    
#### 3.2.2  NativeDaemonConnector

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    NativeDaemonConnector(INativeDaemonConnectorCallbacks callbacks, String socket,
            int responseQueueSize, String logTag, int maxLogSize, PowerManager.WakeLock wl) {
        // callbacks为MountService类对象
        this(callbacks, socket, responseQueueSize, logTag, maxLogSize, wl,
                FgThread.get().getLooper());
    }


    NativeDaemonConnector(INativeDaemonConnectorCallbacks callbacks, String socket,
            int responseQueueSize, String logTag, int maxLogSize, PowerManager.WakeLock wl,
            Looper looper) {
        // mCallbacks为MountService类对象
        mCallbacks = callbacks;
        mSocket = socket;
        // 创建一个用于缓存消息的队列
        mResponseQueue = new ResponseQueue(responseQueueSize);
        mLooper = looper;
        mSequenceNumber = new AtomicInteger(0);
        mLocalLog = new LocalLog(maxLogSize);
    }
    
NativeDaemonConnector继承于Runnable, 所以当MountService里与vold通信的线程运行内容由NativeDaemonConnector实现。

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    public void run() {
        // 构建处理消息的handler, 消息的处理同样由NativeDaemonConnector自己实现
        mCallbackHandler = new Handler(mLooper, this);
        
        while (true) {
            try {
                // 开始监听socket，接收由vold进程发上来的socket消息
                listenToSocket();
            } catch (Exception e) {
                SystemClock.sleep(5000);
            }
        }
    }

#### 3.2.3  监听socket

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    private void listenToSocket() throws IOException {
        LocalSocket socket = null;
        try {
            socket = new LocalSocket();
            LocalSocketAddress address = determineSocketAddress();
            // 建立与vold的socket连接
            socket.connect(address);
            InputStream inputStream = socket.getInputStream();
            synchronized (mDaemonLock) {
                mOutputStream = socket.getOutputStream();
            }
            mCallbacks.onDaemonConnected();
            
            while(true) {
                int count = inputStream.read(buffer, start, BUFFER_SIZE - start);
                ... ...
                // 对收到的消息字符串进行解析，得到一个NativeDaemonEvent对象
                final NativeDaemonEvent event = NativeDaemonEvent.parseRawEvent(
                                    rawEvent);
                if (event.isClassUnsolicited()) {
                    // 处理vold应答码在600-700区间的消息，
                    // 这种消息都是由vold主动发送上来的
                    if (mCallbacks.onCheckHoldWakeLock(event.getCode())
                            && mWakeLock != null) {
                        mWakeLock.acquire();
                        releaseWl = true;
                    }
                    // 最终调用MountService的onEvent()处理
                    if (mCallbackHandler.sendMessage(mCallbackHandler.obtainMessage(
                            event.getCode(), event.getRawEvent()))) {
                        releaseWl = false;
                    }
                } else {
                    //其余的消息都是由MountService主动发送命令给vold后的返回值，一般之前会阻塞在execute()里
                    // 见3.3.1里executeForList()
                    mResponseQueue.add(event.getCmdNumber(), event);
                }
            }
        }
    }
    
#### 3.2.4 消息应答码

* 100 series: 请求操作已初始化, 收到部分响应. 在处理下一个新命令前,期待收到另一个响应消息
* 200 series: 请求操作被vold执行成功
* 400 series: 命令被vold收到，但是请求操作未生效
* 600 series: 由vold根据底层状态变化主动发送来的广播 


MountService的构造函数内容很简单，主要是创建了几个消息循环的handler，并创建了用于和vold进程通信的NativeDaemonConnector对象和线程。
NativeDaemonConnector对象用于和vold进程通信，接收vold发送上来的消息，并且向vold进程发送命令。

### 3.3 MountService.SystemReady()

#### 3.3.1 MountService发送命令

[frameworks/base/services/core/java/com/android/server/MountService.java]

    private void systemReady() {
        mSystemReady = true;
        // 向消息循环队列中发送H_SYSTEM_READY消息
        // mHandler是MountServiceHandler的父类
        mHandler.obtainMessage(H_SYSTEM_READY).sendToTarget();
    }

响应函数就是MountServiceHandler类的handleMessage()方法，

[frameworks/base/services/core/java/com/android/server/MountService.java]

    class MountServiceHandler extends Handler {
        public MountServiceHandler(Looper looper) {
            super(looper);
        }
        
        public void handleMessage(Message msg) {
        switch (msg.what) {
            case H_SYSTEM_READY: {
                handleSystemReady();
                break;
            }
            ... ...   
    }


    private void handleSystemReady() {
        synchronized (mLock) {
            // 通过NativeDaemonConnector对象发送volume reset命令给vold进程
            // 最终调用的是mConnector.execute("volume", "reset")发送命令
            resetIfReadyAndConnectedLocked();
        }
        // 每隔一天发送一次fstrim命令
        MountServiceIdler.scheduleIdlePass(mContext);
    }

#### 3.3.2 NativeDaemonConnector转发

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    public NativeDaemonEvent execute(String cmd, Object... args)
            throws NativeDaemonConnectorException {
        // 使用的命令执行默认超时时间是1分钟
        return execute(DEFAULT_TIMEOUT, cmd, args);
    }


    public NativeDaemonEvent execute(long timeoutMs, String cmd, Object... args)
            throws NativeDaemonConnectorException {
        final NativeDaemonEvent[] events = executeForList(timeoutMs, cmd, args);
        if (events.length != 1) {
            throw new NativeDaemonConnectorException(
                    "Expected exactly one response, but received " + events.length);
        }
        return events[0];
    }
    
最终命令是通过executeForList()发送下去的。

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    public NativeDaemonEvent[] executeForList(long timeoutMs, String cmd, Object... args)
            throws NativeDaemonConnectorException {
        final long startTime = SystemClock.elapsedRealtime();
        
        final ArrayList<NativeDaemonEvent> events = Lists.newArrayList();
        
        final StringBuilder rawBuilder = new StringBuilder();
        final StringBuilder logBuilder = new StringBuilder();
        // 生成命令序列号，MountService发送给vold进程的每条命令都有个序列号，从1开始增加
        final int sequenceNumber = mSequenceNumber.incrementAndGet();
        // 构造命令，将参数传进来的命令组成字符串发送
        makeCommand(rawBuilder, logBuilder, sequenceNumber, cmd, args);
        
        final String rawCmd = rawBuilder.toString();
        final String logCmd = logBuilder.toString();
        
        // 向socket中写数据，和vold进程通信，这里发的是volume reset
        mOutputStream.write(rawCmd.getBytes(StandardCharsets.UTF_8));
        
        NativeDaemonEvent event = null;
        do {
            // 阻塞在mResponseQueue， 等到listenToSocket线程里接收vold发送消息
            event = mResponseQueue.remove(sequenceNumber, timeoutMs, logCmd);
            events.add(event);
        } while (event.isClassContinue());  // 一直等到vold返回码是成功或失败才退出
        
        return events.toArray(new NativeDaemonEvent[events.size()]);
    }
    
MountService在systemReady()之后，做的第一件事，就是发送 "volume reset"给vold进程，这条命令做了很重要的事。

## 4 与vold交互

### 4.1 开机挂载内置存储

上一节最后说到MountService.systemReady()里向vold进程发送了 "volume reset" 命令。这个命令会导致已经存在的存储设备被挂载。
包括内置存储，U盘，EMMC。这里以内置存储和USB Disk为例说明。

#### 4.1.1 Vold响应命令

MountService发送给vold的命令，是通过/dev/socket/vold这个socket节点发送的，最终的处理函数在 FrameworkListener.cpp。

[system/core/libsysutils/src/FrameworkListener.cpp]

    void FrameworkListener::dispatchCommand(SocketClient *cli, char *data) {
        ... ...
        
        for (i = mCommands->begin(); i != mCommands->end(); ++i) {
            FrameworkCommand *c = *i;
            // 从mCommands键表中查找“voldme”命令所代表的对象
            if (!strcmp(argv[0], c->getCommand())) {
                // 如果找到了，通过runCommand()执行命令
                if (c->runCommand(cli, argc, argv)) {
                    SLOGW("Handler '%s' error (%s)", c->getCommand(), strerror(errno));
                }
                goto out;
            }
        }
        
        ... ...
    }
    
[system/vold/CommandListener.cpp]

    int CommandListener::VolumeCmd::runCommand(SocketClient *cli,
                                           int argc, char **argv) {
        if (argc < 2) {
            // 参数不对，发送失败返回码给MountService
            cli->sendMsg(ResponseCode::CommandSyntaxError, "Missing Argument", false);
            return 0;
        }
        
        VolumeManager *vm = VolumeManager::Instance();
        
        std::string cmd(argv[1]);
        if (cmd == "reset") {   // "volume reset"命令
            // 根据vm->reset()的执行结果，向MountService返回返回码
            return sendGenericOkFail(cli, vm->reset());
        } else if(cmd == "shutdown") {
            ... ...
        }
        
        ... ...
    }

[system/vold/VolumeManager.cpp]

    int VolumeManager::reset() {
        // 如果内置存储有mount过，先umount
        mInternalEmulated->destroy();
        // 再调用create()函数，create()父类VolumeBase.cpp
        mInternalEmulated->create();
        for (auto disk : mDisks) {
            // 遍历mDisks链表，重新destroy()和create()
            disk->destroy();
            disk->create();
        }
        mAddedUsers.clear();
        mStartedUsers.clear();
        return 0;
    }
    
[system/vold/VolumeBase.cpp]

VolumeBase::create()在之前的VolumeManager启动时分析过，不同的地方在于这次发送的返回码会被MountService收到。

    status_t VolumeBase::create() {
        mCreated = true;
        status_t res = doCreate();
        // 再次发送返回码，这次MountService会有响应, 发送"volume mount emulated"命令给vold
        notifyEvent(ResponseCode::VolumeCreated,
                StringPrintf("%d \"%s\" \"%s\"", mType, mDiskId.c_str(), mPartGuid.c_str()));
        setState(State::kUnmounted);
        return res;
    }
    
再看看对mDisks键表中进行create(), 如果开机时插入的有U盘或EMMC卡之类的，这里就会重新挂载。

[system/vold/Disk.cpp]

    status_t Disk::create() {
        mCreated = true;
        notifyEvent(ResponseCode::DiskCreated, StringPrintf("%d", mFlags));
        readMetadata();
        // 通过sgdisk --android-dump 命令，来决定如何创建分区并挂载
        readPartitions();
        return OK;
    }
    
[system/vold/Disk.cpp]

    status_t Disk::readPartitions() {
        // 读取磁盘的分区表信息
        std::vector<std::string> cmd;
        cmd.push_back("/system/bin/sgdisk");
        cmd.push_back("--android-dump");
        cmd.push_back(mDevPath);
        
        std::vector<std::string> output;
        // 在新的进程中执行sgdisk命令
        status_t res = ForkExecvp(cmd, output);
        
        if (!strcmp(token, "DISK")) {
            // 分区表类型，mbr稍微比较常用一些
            const char* type = strtok(nullptr, kSgdiskToken);
            if (!strcmp(type, "mbr")) {
                table = Table::kMbr;
            } else if (!strcmp(type, "gpt")) {
                table = Table::kGpt;
            }
        } else if (!strcmp(token, "PART")) {
            dev_t partDevice = makedev(major(mDevice), minor(mDevice) + i);
            if (table == Table::kMbr) {
                const char* type = strtok(nullptr, kSgdiskToken);
                switch (strtol(type, nullptr, 16)) {
                case 0x06: // FAT16
                case 0x0b: // W95 FAT32 (LBA)
                case 0x0c: // W95 FAT32 (LBA)
                case 0x0e: // W95 FAT16 (LBA)
                case 0x07: // NTFS EXFAT
                case 0x83: // EXT2 EXT3 EXT4
                    foundParts = true;
                    // 对于上面这些格式的分区，创建PublicVolume
                    createPublicVolume(partDevice);
                    break;
                }
            }
        }
    }

[system/vold/Disk.cpp]

    void Disk::createPublicVolume(dev_t device) {
        // new一个PublicVolume()的对象
        auto vol = std::shared_ptr<VolumeBase>(new PublicVolume(device));
        // 存入mVolumes
        mVolumes.push_back(vol);
        vol->setDiskId(getId());
        // 调用复写的PublicVolume::doCreate()函数创建设备结点
        vol->create();
    }

当vold接收到"volume reset"后，对内置存储设备和每个Disk都重新create()一次，这样可以保证让MountService收到vold返回的状态。
做这样一个动作实际上就是MountService启动之后，想要拿到当前所有磁盘和分区的信息。

#### 4.1.2 MountService接收返回码

当调用EmulatedVolume::create()时，vold会向MountService发送返回值ResponseCode::VolumeCreated[650]和ResponseCode::VolumeStateChanged[651]。

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    private void listenToSocket() throws IOException {
        ... ... 
        
        for (;;) {
            final NativeDaemonEvent event = NativeDaemonEvent.parseRawEvent(
                                    rawEvent);
            log("RCV <- {" + event + "}");
            
            if (event.isClassUnsolicited()) {   // 650和651都属于这一类
                if (mCallbacks.onCheckHoldWakeLock(event.getCode())
                        && mWakeLock != null) {
                    mWakeLock.acquire();
                    releaseWl = true;
                }
                // 通过mCallbackHandler发送消息
                if (mCallbackHandler.sendMessage(mCallbackHandler.obtainMessage(
                        event.getCode(), event.getRawEvent()))) {
                    releaseWl = false;
                }
            } else {    // 最后的成功或失败的返回码200和400属于这里
                mResponseQueue.add(event.getCmdNumber(), event);
            }
        }
        
        ... ...
    }

[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    public boolean handleMessage(Message msg) {
        String event = (String) msg.obj;
        try {
            // mCallbacks就是MountService, 相当于调用MountService.java里的onEvent()处理消息
            if (!mCallbacks.onEvent(msg.what, event, NativeDaemonEvent.unescapeArgs(event))) {
                log(String.format("Unhandled event '%s'", event));
            }
        } catch (Exception e) {
            loge("Error handling '" + event + "': " + e);
        } finally {
            if (mCallbacks.onCheckHoldWakeLock(msg.what) && mWakeLock != null) {
                mWakeLock.release();
            }
        }
        return true;
    }
    
[frameworks/base/services/core/java/com/android/server/MountService.java]

    public boolean onEvent(int code, String raw, String[] cooked) {
        synchronized (mLock) {
            return onEventLocked(code, raw, cooked);
        }
    }


    private boolean onEventLocked(int code, String raw, String[] cooked) {
        switch (code) {
            case VoldResponseCode.VOLUME_CREATED: {     // code = 650
                final String id = cooked[1];
                final int type = Integer.parseInt(cooked[2]);
                final String diskId = TextUtils.nullIfEmpty(cooked[3]);
                final String partGuid = TextUtils.nullIfEmpty(cooked[4]);
                
                final DiskInfo disk = mDisks.get(diskId);
                // 新建一个VolumeInfo对象
                final VolumeInfo vol = new VolumeInfo(id, type, disk, partGuid);
                mVolumes.put(id, vol);
                onVolumeCreatedLocked(vol);
                break;
            }
            
            ... ...
        }
    }


    private void onVolumeCreatedLocked(VolumeInfo vol) {
        if (vol.type == VolumeInfo.TYPE_EMULATED) {
            vol.mountFlags |= VolumeInfo.MOUNT_FLAG_PRIMARY;
                vol.mountFlags |= VolumeInfo.MOUNT_FLAG_VISIBLE;
                // 通过MountServiceHandler向vold发送mount消息
                mHandler.obtainMessage(H_VOLUME_MOUNT, vol).sendToTarget();
        }
    }
    
通过MountServiceHandler向vold进程发送mount消息。

[frameworks/base/services/core/java/com/android/server/MountService.java]

    class MountServiceHandler extends Handler {
        public void handleMessage(Message msg) {
            case H_VOLUME_MOUNT: {
                ... ...
                
                final VolumeInfo vol = (VolumeInfo) msg.obj;
                // 通过NativeDaemonConnector向vold发送 "volume mount"消息
                mConnector.execute("volume", "mount", vol.id, vol.mountFlags,
                        vol.mountUserId);
                break;
            }
            
            ... ...
        }
    }
    
#### 4.1.3 vold处理mount消息

vold接收到 "volume mount"消息后，会找到volumeCmd

[system/vold/CommandListener.cpp]

    int CommandListener::VolumeCmd::runCommand(SocketClient *cli,
                            int argc, char **argv) {
        ... ...
        
        if (cmd == "mount" && argc > 2) {
        std::string id(argv[2]);
        // 通过volume id找到对应的Volume类对象
        auto vol = vm->findVolume(id);
        int mountFlags = (argc > 3) ? atoi(argv[3]) : 0;
        userid_t mountUserId = (argc > 4) ? atoi(argv[4]) : -1;
        
        vol->setMountFlags(mountFlags);
        vol->setMountUserId(mountUserId);
        
        // 调用各自volumeBase对象的mount()函数进行mount
        // 对于内置存储，最终调的是EmulatedVolume::doMount()
        // 对于USB DISK，最终调用的是PublicVolume::doMount()
        int res = vol->mount();
        if (mountFlags & android::vold::VolumeBase::MountFlags::kPrimary) {
            // 对于内置存储，需要设置标记标明它是主存储区
            vm->setPrimary(vol);
        }
        return sendGenericOkFail(cli, res);
    }
        ... ...
    }
    
对于内置存储器，EmulatedVolume.cpp实现在doMount()虚函数。

[system/vold/VolumeBase.cpp]

    status_t VolumeBase::mount() {
        setState(State::kChecking);
        // EmulatedVolume.cpp重写了doMount()虚函数
        status_t res = doMount();
        if (res == OK) {
            // mount成功后，设置状态为State::kMounted，同时发送ResponseCode::VolumeStateChanged[651]给MountService
            setState(State::kMounted);
        } else {
            setState(State::kUnmountable);
        }
    
        return res;
    }

[system/vold/EmulatedVolume.cpp]

    status_t EmulatedVolume::doMount() {
        const char* kFusePath = "/system/bin/sdcard";
        // 通过sdcard命令，使用fuse文件系统，让sdcard分区和data共用一个分区
        if (!(mFusePid = fork())) {     // 创建一个单独的线程执行sdcard命令
            if (execl(kFusePath, kFusePath,
                    "-u", "1023", // AID_MEDIA_RW
                    "-g", "1023", // AID_MEDIA_RW
                    "-m",
                    "-w",
                    mRawPath.c_str(),
                    label.c_str(),
                    NULL)) {
            }
        }
    }
    
如果mount成功，若执行成功，vold进程会通过/dev/socket/vold向MountService发送表示成功的返回码200。

[system/vold/CommandListener.cpp]

    int CommandListener::sendGenericOkFail(SocketClient *cli, int cond) {
        if (!cond) {
            // 返回码是200， 表明这条命令执行成功，表示MountService的一次命令周期结束
            return cli->sendMsg(ResponseCode::CommandOkay, "Command succeeded", false);
        } else {
            // 返回码是400，命令执行失败
            return cli->sendMsg(ResponseCode::OperationFailed, "Command failed", false);
        }
    }

NativeDaemonConnector收到200的返回码时，往消息队列mResponseQueue中添加一项，然后MountService的发送消息线程在execute()里唤醒。
    
[frameworks/base/services/core/java/com/android/server/NativeDaemonConnector.java]

    private void listenToSocket() throws IOException {
        ... ... 
        
        for (;;) {
            final NativeDaemonEvent event = NativeDaemonEvent.parseRawEvent(
                                    rawEvent);
            log("RCV <- {" + event + "}");
            
            if (event.isClassUnsolicited()) {   // 650和651都属于这一类
                if (mCallbacks.onCheckHoldWakeLock(event.getCode())
                        && mWakeLock != null) {
                    mWakeLock.acquire();
                    releaseWl = true;
                }
                // 通过mCallbackHandler发送消息
                if (mCallbackHandler.sendMessage(mCallbackHandler.obtainMessage(
                        event.getCode(), event.getRawEvent()))) {
                    releaseWl = false;
                }
            } else {    // 最后的成功或失败的返回码200和400属于这里
                mResponseQueue.add(event.getCmdNumber(), event);
            }
        }
        
        ... ...
    }
    

    public NativeDaemonEvent[] executeForList(long timeoutMs, String cmd, Object... args)
    {
        do {
            event = mResponseQueue.remove(sequenceNumber, timeoutMs, logCmd);
            events.add(event);
        } while (event.isClassContinue());  // 当获取到event里返回码是200的时候，退出循环, 命令执行结束
    }

vold里mount成功之后，会向MountService发送ResponseCode::VolumeStateChanged[651]返回码。MountService接收之后，调用OnEventLocked()处理。

[frameworks/base/services/core/java/com/android/server/MountService.java]

    private boolean onEventLocked(int code, String raw, String[] cooked) {
        case VoldResponseCode.VOLUME_STATE_CHANGED: {
            final VolumeInfo vol = mVolumes.get(cooked[1]);
            if (vol != null) {
                final int oldState = vol.state;
                final int newState = Integer.parseInt(cooked[2]);
                vol.state = newState;
                // 发送Intent.ACTION_MEDIA_MOUNTED广播,SystemUI收到广播后显示U盘弹框
                onVolumeStateChangedLocked(vol, oldState, newState);
            }
            break;
        }
    }

### 4.2 U盘插入

当U盘插入USB接口时，linux kernel会通过socket向vold发送netlink消息。最终调用VolumeManager::handleBlockEvent()进行处理, 具体参考上一篇VOLD启动分析。
接着开始挂载U盘，大概流程和上一节挂载内置存储相似。但是U盘作为PublicVolume挂载，挂载函数是PublicVolume::doMount()。

[system/vold/PublicVolume.cpp]

    status_t PublicVolume::doMount() {
        ... ...
        
        // 依次尝试不同文件系统的挂载，若全部不成功，则挂载失败
        Ntfs::doMount(mDevPath.c_str(), mRawPath.c_str(), false, false, AID_MEDIA_RW, AID_MEDIA_RW, permMask);
        vfat::Mount(mDevPath, mRawPath, false, false, false, AID_MEDIA_RW, AID_MEDIA_RW, permMask, true);
        Extfs::doMount(mDevPath.c_str(), mRawPath.c_str(), false, false, AID_MEDIA_RW, AID_MEDIA_RW, permMask);
        Exfat::doMount(mDevPath.c_str(), mRawPath.c_str(), false, false, false, AID_MEDIA_RW, AID_MEDIA_RW, permMask);
        
        ... ...
    }
    
## 5 小结

MountService和vold作为Android存储系统，所作的工作远不止这些，这里只分析基本的结构和挂载过程，至于其它的功能，在熟知这些之后，很容易举一反三。