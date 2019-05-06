---
layout: post
title:  "Zygote分析(二)"
subtitle: dacaoxin
author: dacaoxin
date:   2016-12-7 20:10:00
catalog:  true
tags:
    - android
    - framework
    - native
    - zygote
---

## 开启新纪元

上一篇中说过，AndroidRuntime.cpp的start()有一个很重要的作用，就是通过JNI机制反调ZygoteInit.java中的main()方法，这个地方也就是开启Android java世界的源头。所以我想大声对世界宣布: "welcome to JAVA world!"

这里需要记住的上，上一篇中提到过，JNI反调JAVA方法时，传入了一个字符串数组作为参数，所以argv[]的值是：com.android.internal.os.ZygoteInit; start-system-server; --abi-list=arm64-v8a; --socket-name=zygote

## 欢迎来到JAVA世界  

我们知道Android中很多重要的进程和应用程序都是由JAVA语言编写的，即然ZygoteInit.java的main()方法作为android中第一个调用的JAVA方法，想必这其中一定有很重要的关系。

[-> framework/base/core/java/com/android/internal/os/ZygoteInit.java]

    public static void main(String argv[])
    {
        for (int i = 1; i < argv.length; i++) {
            if ("start-system-server".equals(argv[i])) {        
                // 传入main()的参数有"start-system-server", 所以 startSystemServer = true;
                startSystemServer = true;
            } else if (argv[i].startsWith(ABI_LIST_ARG)) {
                abiList = argv[i].substring(ABI_LIST_ARG.length());
            } else if (argv[i].startsWith(SOCKET_NAME_ARG)) {
                // 设置socket name 为 zygote
                socketName = argv[i].substring(SOCKET_NAME_ARG.length());
            } else {
                throw new RuntimeException("Unknown command line argument: " + argv[i]);
            }
        }
        // 创建socket通信所需要的节点
        registerZygoteSocket(socketName);
        // 预加载所需要的各种资源，这里也是Android开机慢的一个原因所在
        preload();
        // 启动systemserver进程
        startSystemServer(abiList, socketName);
        // 进入循环，监听socket，并作出相关的动作
        runSelectLoop(abiList);
    }

可以看到，ZygoteInit.main()的主要作用就是：
1. 创建socket通信所需要的套接字，并循环监听
2. 启动systemserver进程, 这个进程中将开启绝大部分android关键的系统服务
3. 预加载所需要的资源  

接下来，我们分别看看这几个功能是怎么实现的。

### 创建socket通信套接字  

[-> framework/base/core/java/com/android/internal/os/ZygoteInit.java]

    private static void registerZygoteSocket(String socketName)
    {
        sServerSocket = new LocalServerSocket(fd);
    }

这个函数比较简单，就是创建一个LocalServerSocket对象进行socket的bind和listen操作。

### 预加载资源  

[-> framework/base/core/java/com/android/internal/os/ZygoteInit.java]

    static void preload() {
        Log.d(TAG, "begin preload");
        preloadClasses();
        preloadResources();
        preloadOpenGL();
        preloadSharedLibraries();
        WebViewFactory.prepareWebViewInZygote();
        Log.d(TAG, "end preload");
    }

没有仔细看，大概就是预加载一些类资源之类的。

### 启动systemserver进程    

这个是zygote的一个重点，详细看看

[-> framework/base/core/java/com/android/internal/os/ZygoteInit.java]

    static boolean startSystemServer(String abiList, String socketName)
    {
        // 定义了systemserver进程的各种信息，比如uid, gid, 进程名字等等
        String args[] = {
            "--setuid=1000",
            "--setgid=1000",
            "--setgroups=1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1018,1021,1032,3001,3002,3003,3006,3007",
            "--capabilities=" + capabilities + "," + capabilities,
            "--nice-name=system_server",
            "--runtime-args",
            "com.android.server.SystemServer",
        };
        
        parsedArgs = new ZygoteConnection.Arguments(args);
        // fork出来systemserver进程
        pid = Zygote.forkSystemServer(
                    parsedArgs.uid, parsedArgs.gid,
                    parsedArgs.gids,
                    parsedArgs.debugFlags,
                    null,
                    parsedArgs.permittedCapabilities,
                    parsedArgs.effectiveCapabilities);
        
        // fork的返回值为0表示是子进程
        if (pid == 0) {
            handleSystemServerProcess(parsedArgs);
        }
    }

可以看到startSystemServer()的主要工作有：
1. fork出一个新的进程，它就是systemserver进程
2. 进入systemserver进程，处理systemserver进程需要做的工作

#### 先来看看zygote是如何fork出systemserver进程的  

[-> frameworks/base/core/java/com/android/internal/os/Zygote.java]

    public static int forkSystemServer(int uid, int gid, int[] gids, int debugFlags,
            int[][] rlimits, long permittedCapabilities, long effectiveCapabilities) {
        VM_HOOKS.preFork();
        // 实际上是通过JNI调用本地方法来fork子进程
        int pid = nativeForkSystemServer(
                uid, gid, gids, debugFlags, rlimits, permittedCapabilities, effectiveCapabilities);
        // Enable tracing as soon as we enter the system_server.
        if (pid == 0) {
            Trace.setTracingEnabled(true);
        }
        VM_HOOKS.postForkCommon();
        return pid;
    }

nativeForkSystemServer()是一个native方法，它实际的实现如下：  

[-> framework/base/core/jni/com_android_internal_os_Zygote.cpp]

    static jint com_android_internal_os_Zygote_nativeForkSystemServer(
            JNIEnv* env, jclass, uid_t uid, gid_t gid, jintArray gids,
            jint debug_flags, jobjectArray rlimits, jlong permittedCapabilities,
            jlong effectiveCapabilities) {
        
        pid_t pid = ForkAndSpecializeCommon(env, uid, gid, gids,
                                      debug_flags, rlimits,
                                      permittedCapabilities, effectiveCapabilities,
                                      MOUNT_EXTERNAL_DEFAULT, NULL, NULL, true, NULL,
                                      NULL, NULL);
        if (pid > 0) {
            // pid是子进程的进程号
            // 这段是父进程执行的代码，即zygote这个进程
            // zygote会停在这里，直到等到子进程systemserver发过来的信号，确保systemserver进程成功
            // 如果不成功，zygote进程会自杀
            // WNOHANG信号: 若pid指定的子进程没有结束，则waitpid()函数返回0，不予以等待。若结束，则返回该子进程的ID。
            if (waitpid(pid, &status, WNOHANG) == pid) {
            ALOGE("System server process %d has died. Restarting Zygote!", pid);
            RuntimeAbort(env);
        }
    }

[-> framework/base/core/jni/com_android_internal_os_Zygote.cpp]

    static pid_t ForkAndSpecializeCommon(JNIEnv* env, uid_t uid, gid_t gid,                                     jintArray javaGids,
                                     jint debug_flags, jobjectArray javaRlimits,
                                     jlong permittedCapabilities, jlong effectiveCapabilities,
                                     jint mount_external,
                                     jstring java_se_info, jstring java_se_name,
                                     bool is_system_server, jintArray fdsToClose,
                                     jstring instructionSet, jstring dataDir) 
    {
        // 设置进程对信号的处理
        SetSigChldHandler();
        pid_t pid = fork();     // 最终还是调用Linux的fork()函数创建进程
        if (pid == 0)
        {
            ... ... // 对子进程做一些处理，比如设置 uid, gid之类
        }
    }

再来看看SetSigChldHandler()函数，

[-> framework/base/core/jni/com_android_internal_os_Zygote.cpp]

    static void SetSigChldHandler() {
        struct sigaction sa;
        memset(&sa, 0, sizeof(sa));
        sa.sa_handler = SigChldHandler;
        // 让zygote进程接收SIGCHLD信号
        // 当一个进程终止或停止时，子进程会将SIGCHLD信号发送给父进程，系统默认会忽略掉这个信号
        // 通过sigaction可以让父进程捕捉这个信号
        int err = sigaction(SIGCHLD, &sa, NULL);
        if (err < 0) {
            ALOGW("Error setting SIGCHLD handler: %d", errno);
        }
    }
    
    static void SigChldHandler(int /*signal_number*/) {
        while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
            if (pid == gSystemServerPid) {
                // 这里当子进程systemserver停止了，zygote也会自杀
                ALOGE("Exit zygote because system server (%d) has terminated");
                kill(getpid(), SIGKILL);
            }
        }
    }

可以看出来，zygote最终也是通过fork()函数衍生出子进程systemserver的，然将自己的生命和systemserver绑定到一起，两者共进退

#### 进入systemserver进程，完成systemserver的工作    

当systemserver进程创建成功之后，它便与父亲zygote各行其道，开始了自力更生之路。

[-> frameworks/base/core/java/com/android/internal/os/ZygoteInit.java]

    private static void handleSystemServerProcess(
            ZygoteConnection.Arguments parsedArgs)
            throws ZygoteInit.MethodAndArgsCaller
    {
        // 因为是zygote的子进程，所以会继承父亲的一些全局变量，在这里不再监听socket
        closeServerSocket();
        // 更改自己的进程名字
        Process.setArgV0(parsedArgs.niceName);
        // 对SYSTEMSERVERCLASSPATH环境变量里设置的jar包进行dex-opt
        // 它最终也是通过socket向installd发消息来进行jar包rdex-opt
        final String systemServerClasspath = Os.getenv("SYSTEMSERVERCLASSPATH");
        if (systemServerClasspath != null) {
            performSystemServerDexOpt(systemServerClasspath);
        }
        
        // 这里parsedArgs.remainingArgs = com.android.server.SystemServer
        RuntimeInit.zygoteInit(parsedArgs.targetSdkVersion,parsedArgs.remainingArgs, cl);
    }
    
[-> frameworks/base/core/java/com/android/internal/os/RuntimeInit.java]

    public static final void zygoteInit(int targetSdkVersion, String[] argv, ClassLoader classLoader){
        
        redirectLogStreams();
        
        commonInit();
        // native函数
        nativeZygoteInit();
        // 从这里进入systemserver.java的main()函数
        applicationInit(targetSdkVersion, argv, classLoader);
    }

nativeZygoteInit()是一个native函数，根据jni的知识，可以找到最终调用的是，

[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    static void com_android_internal_os_RuntimeInit_nativeZygoteInit(JNIEnv* env, jobject clazz)
    {
        gCurRuntime->onZygoteInit();
    }    
    
gCurRuntime又是什么呢，看看AndroidRuntime的构造函数，

[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    AndroidRuntime::AndroidRuntime(char* argBlockStart, const size_t argBlockLength) :
        mExitWithoutCleanup(false),
        mArgBlockStart(argBlockStart),
        mArgBlockLength(argBlockLength)
    {
        // Pre-allocate enough space to hold a fair number of options.
        mOptions.setCapacity(20);
        
        assert(gCurRuntime == NULL);        // one per process
        gCurRuntime = this;
    }

由于AppRuntime继承了AndroidRuntime, 所以gCurRuntime就是AppRuntime对象，并且onZygoteInit()是虚函数，又在AppRuntime中实现了，所以，

[-> frameworks/base/cmds/app_process/app_main.cpp]

    virtual void onZygoteInit()
    {
        // ProcessState与binder有关   
        sp<ProcessState> proc = ProcessState::self();
        ALOGV("App process: starting thread pool.\n");
        proc->startThreadPool();
    }

也就是说，在commonInit()之后，systemserver进程也就可以使用binder通信了。

接着看applicationInit()方法，

[-> frameworks/base/core/java/com/android/internal/os/RuntimeInit.java]

    private static void applicationInit(int targetSdkVersion, String[] argv, ClassLoader classLoader) throws ZygoteInit.MethodAndArgsCaller {
        VMRuntime.getRuntime().setTargetHeapUtilization(0.75f);
        VMRuntime.getRuntime().setTargetSdkVersion(targetSdkVersion);
        // args.startClass = com.android.server.SystemServer
        invokeStaticMain(args.startClass, args.startArgs, classLoader);
    }
    
[-> frameworks/base/core/java/com/android/internal/os/RuntimeInit.java]

    private static void invokeStaticMain(String className, String[] argv, ClassLoader classLoader) throws ZygoteInit.MethodAndArgsCaller {
        // 通过反射找到systemserver的类
        cl = Class.forName(className, true, classLoader);
        // 找到systemserver的main()函数
        m = cl.getMethod("main", new Class[] { String[].class });
        throw new ZygoteInit.MethodAndArgsCaller(m, argv);
    }
    
也就是说接着看applicationInit()最终抛出了一个ZygoteInit.MethodAndArgsCaller类型的异常。这个异常在哪里被捕获呢？一层一层的返回函数调用关系，会发现在ZygoteInit.java的main()方法中被捕获。

> 需要注意的是，此时是在fork()之后，也就是在systemserver进程中才会捕获这个异常

再来看看MethodAndArgsCaller的run()方法：  

[-> frameworks/base/core/java/com/android/internal/os/ZygoteInit.java]

    public void run() {
        try {
            // mMethod就是SystemServer.java中的main()方法
            // java中通过invoke进行反射调用
            mMethod.invoke(null, new Object[] { mArgs });
        } catch (IllegalAccessException ex) {
            throw new RuntimeException(ex);
        } catch (InvocationTargetException ex) {
            Throwable cause = ex.getCause();
            if (cause instanceof RuntimeException) {
                throw (RuntimeException) cause;
            } else if (cause instanceof Error) {
                throw (Error) cause;
            }
            throw new RuntimeException(ex);
        }
    }

### 监听socket消息，并执行相应的操作

在ZygoteInit.java的main()函数最后，调用了runSelectLoop()方法进入循环中对socket进行监听。

[-> frameworks/base/core/java/com/android/internal/os/ZygoteInit.java]

    private static void runSelectLoop(String abiList) throws MethodAndArgsCaller {
    {
        while (true) {
            fdArray = fds.toArray(fdArray);
            // native函数实现的select机制
            index = selectReadable(fdArray);
            
            if (index < 0) {
                throw new RuntimeException("Error in select()");
            } else if (index == 0) {
                ZygoteConnection newPeer = acceptCommandPeer(abiList);
                peers.add(newPeer);
                fds.add(newPeer.getFileDescriptor());
            } else {
                boolean done;
                // 当有请求发来时，调用ZygoteConnection的runOnce方法
                done = peers.get(index).runOnce();
                
                if (done) {
                    peers.remove(index);
                    fds.remove(index);
                }
            }
        }
    }
    
selectReadable()是一个native函数，由JNI知识可以找到他的实现，

[-> frameworks/base/core/jni/com_android_internal_os_ZygoteInit.cpp]

    static jint com_android_internal_os_ZygoteInit_selectReadable (
        JNIEnv *env, jobject clazz, jobjectArray fds)
    {
        FD_ZERO(&fdset);
        err = select (nfds, &fdset, NULL, NULL, NULL);
        if (FD_ISSET(fd, &fdset)) {
            return (jint)i;
        }
    }
    
所以实际上就是调用linux的select()函数实现socket的监听。当接收到有请求时，会调用ZygoteConnection的runOnce()方法。

[-> frameworks/base/core/java/com/android/internal/os/ZygoteConnection.java]

    boolean runOnce() throws ZygoteInit.MethodAndArgsCaller {
        // 再次调用fork创建一个子进程
        pid = Zygote.forkAndSpecialize(parsedArgs.uid, parsedArgs.gid, parsedArgs.gids,
                    parsedArgs.debugFlags, rlimits, parsedArgs.mountExternal, parsedArgs.seInfo,
                    parsedArgs.niceName, fdsToClose, parsedArgs.instructionSet,
                    parsedArgs.appDataDir);
        if (pid == 0) {
            // 处理子进程的工作
            handleChildProc(parsedArgs, descriptors, childPipeFd, newStderr);
        }
    }
    
[-> frameworks/base/core/java/com/android/internal/os/ZygoteConnection.java]

    private void handleChildProc(Arguments parsedArgs, FileDescriptor[] descriptors, FileDescriptor pipeFd, PrintStream newStderr) {
        closeSocket();
        ZygoteInit.closeServerSocket();
        // 设置进程名字
        Process.setArgV0(parsedArgs.niceName);
        // 再次调用RuntimeInit的zygoteInit方法，这里就和创建systemserver一样了
        RuntimeInit.zygoteInit(parsedArgs.targetSdkVersion,
                        parsedArgs.remainingArgs, null /* classLoader */);
    }
    
zygote中分裂其他的进程时，最终也是和systemserver类似，关于这里下一节中会通过举例来说明

