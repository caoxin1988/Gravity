---
layout: post
title:  "Zygote分析(三)"
subtitle: dacaoxin
author: dacaoxin
date:   2016-12-12 22:20:00
catalog:  true
tags:
    - android
    - framework
    - native
    - zygote
---

这里通过两个常用的例子来感受并理解一下Zygote作为进程孵化器的巨大作用。    

# JAVA实现的shell命令  

## pm命令    

在平时开发的过程中，经常会使用pm install xxx.apk之类的命令，其实pm命令也是通过zygote来做事的。pm命令可以执行，一定是在system/bin下面有一个可执行文件叫pm。先看看它的Makefile.

### pm编译脚本    

[-> frameworks/base/cmds/pm/Android.mk]

    LOCAL_PATH:= $(call my-dir)
    include $(CLEAR_VARS)
    
    LOCAL_SRC_FILES := $(call all-subdir-java-files)
    LOCAL_MODULE := pm
    include $(BUILD_JAVA_LIBRARY)
    
    include $(CLEAR_VARS)
    ALL_PREBUILT += $(TARGET_OUT)/bin/pm
    $(TARGET_OUT)/bin/pm : $(LOCAL_PATH)/pm | $(ACP)
        $(transform-prebuilt-to-target)

这里做了两件事：
1. 编译出一个pm.jar的包
2. 把源码根目录下的pm脚本拷贝到image的/system/bin目录下

### pm命令执行

所以每次执行pm命令的时候，实际上先运行的是/system/bin下面的pm脚本。

[-> frameworks/base/cmds/pm/pm]

    base=/system
    export CLASSPATH=$base/framework/pm.jar
    exec app_process $base/bin com.android.commands.pm.Pm "$@"

它首先export一个pm.jar的jar包到CLASSPATH环境变量，然后执行app_process。app_process在"zygote分析(一)"中有提过，它的入口就是App_main.cpp。
这里就见识到app_process的强大的功能，它可以启动任意的java程序。同时也是给我们提供了解决问题的另一种思路。在我们一般的想法中，在shell里执行的命令，一般都是通过C/C++来实现，而现在有了app_process之后，我们可以调用JAVA的代码来实现我们想要的工作。

## 通过app_process起启com.android.commands.pm.Pm    

app_process执行流程和第一篇中的类似，只不过有一些细微的差别，这里只列出来这次执行的代码。以下面这条命令为例:

> pm list packages  

实际上它执行的是

> app_process $base/bin com.android.commands.pm.Pm  pm  list packages

[-> frameworks/base/cmds/app_process/app_main.cpp]

    int main(int argc, char* const argv[])
    {
        while (i < argc) {
            const char* arg = argv[i++];
    		ALOGD("i = %d, arg = %s", i,  arg);
            if (strcmp(arg, "--zygote") == 0) {
                zygote = true;
                niceName = ZYGOTE_NICE_NAME;
            } else if (strcmp(arg, "--start-system-server") == 0) {
                startSystemServer = true;
            } else if (strcmp(arg, "--application") == 0) {
                application = true;
            } else if (strncmp(arg, "--nice-name=", 12) == 0) {
                niceName.setTo(arg + 12);
            } else if (strncmp(arg, "--", 2) != 0) {
    			// 满足这个if的条件，把className的值设为com.android.commands.pm.Pm
                className.setTo(arg);
                break;
            } else {
                --i;
                break;
            }
        }
        
        Vector<String8> args;
        if (!className.isEmpty()) {     // className非空，走这个分支
            // 这里分设置全局变量mClassName, mArgs; 这两个变量为后面调用Pm.java作准备
            args.add(application ? String8("application") : String8("tool"));
            runtime.setClassNameAndArgs(className, argc - i, argv + i);
        } else {    // 这里是篇一中走的路径，也就是在zygote模式
            ... ... 
        }
        
        if (zygote) {   // 非zygote模式
            runtime.start("com.android.internal.os.ZygoteInit", args, zygote);
        } else if (className) {	    // 这次走这个分支, 直接进入RuntimeInit.java的main()函数
            runtime.start("com.android.internal.os.RuntimeInit", args, zygote);
        } else {
            fprintf(stderr, "Error: no class name or --zygote supplied.\n");
            app_usage();
            LOG_ALWAYS_FATAL("app_process: no class name or --zygote supplied.");
            return 10;
        }
    }

到这里，其实主要就是设置了几个关键变量的值：mClassName = className = com.android.commands.pm.Pm; mArgs = list, packages; args = tool；
然后通过start()函数启动RuntimeInit.java的main()函数

[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    void AndroidRuntime::start(const char* className, const Vector<String8>& options, bool zygote)
    {
        // className = com.android.commands.pm.Pm
        // options.size = 1, option[0] = tool
        JNIEnv* env;
        // 启动虚拟机，这个进程拥有自己的虚拟机
        if (startVm(&mJavaVM, &env, zygote) != 0) {
            return;
        }
        // 虚函数，实现在AppRuntime类里, 这里给mClass赋值，为后面调用Pm.java做准备
        onVmCreated(env);
        // 注册JNI函数，这个进程可以调用JNI方法
        startReg(env);
        
        // 下面这段构造参数给RuntimeInit.java的main()方法
        // strArray = com.android.commands.pm.Pm, tool
        stringClass = env->FindClass("java/lang/String");
        assert(stringClass != NULL);
        strArray = env->NewObjectArray(options.size() + 1, stringClass, NULL);
        assert(strArray != NULL);
        classNameStr = env->NewStringUTF(className);
        assert(classNameStr != NULL);
        env->SetObjectArrayElement(strArray, 0, classNameStr);
        for (size_t i = 0; i < options.size(); ++i) {
            jstring optionsStr = env->NewStringUTF(options.itemAt(i).string());
            assert(optionsStr != NULL);
            env->SetObjectArrayElement(strArray, i + 1, optionsStr);
        }
        
        // 通过JNI方法调用RuntimeInit.java的main()方法
        char* slashClassName = toSlashClassName(className);
        jclass startClass = env->FindClass(slashClassName);
        jmethodID startMeth = env->GetStaticMethodID(startClass, "main", "([Ljava/lang/String;)V");
        env->CallStaticVoidMethod(startClass, startMeth, strArray);
    }
    
[-> frameworks/base/cmds/app_process/app_main.cpp]

    virtual void onVmCreated(JNIEnv* env)
    {
        if (mClassName.isEmpty()) {
            return; // Zygote. Nothing to do here.
        }
        
        char* slashClassName = toSlashClassName(mClassName.string());
        mClass = env->FindClass(slashClassName);
        if (mClass == NULL) {
            ALOGE("ERROR: could not find class '%s'\n", mClassName.string());
        }
        free(slashClassName);
        
        mClass = reinterpret_cast<jclass>(env->NewGlobalRef(mClass));
    }
    
onVmCreated()其实就是找到mClassName中的包名的类对象，然后存到mClass变量里，方面后面通过JNI调用JAVA方法。

接着进入RuntimeInit.java的main()方法:

[-> frameworks/base/core/java/com/android/internal/os/RuntimeInit.java]

    public static final void main(String[] argv) {
        if (argv.length == 2 && argv[1].equals("application")) {
            if (DEBUG) Slog.d(TAG, "RuntimeInit: Starting application");
            redirectLogStreams();
        } else {
            if (DEBUG) Slog.d(TAG, "RuntimeInit: Starting tool");
        }
        commonInit();
        
        // 这个函数做了重要的事情
        nativeFinishInit();
    }
    
nativeFinishInit()是个native方法，它的实现如下：

[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    static void com_android_internal_os_RuntimeInit_nativeFinishInit(JNIEnv* env, jobject clazz)
    {
        // gCurRuntime是一个AppRuntime对象
        gCurRuntime->onStarted();
    }
    
[-> frameworks/base/cmds/app_process/app_main.cpp]

    virtual void onStarted()
    {
        sp<ProcessState> proc = ProcessState::self();
        ALOGV("App process: starting thread pool.\n");
        proc->startThreadPool();
        
        AndroidRuntime* ar = AndroidRuntime::getRuntime();
        // 设用callMain()函数，它的实现在AndroidRuntime.cpp里
        ar->callMain(mClassName, mClass, mArgs);
        
        IPCThreadState::self()->stopProcess();
    }
    
[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    status_t AndroidRuntime::callMain(const String8& className, jclass clazz, const Vector<String8>& args)
    {
        JNIEnv* env;
        jmethodID methodId;
        
        // 获取JNIEnv变量
        env = getJNIEnv();
        methodId = env->GetStaticMethodID(clazz, "main", "([Ljava/lang/String;)V");
        // 能过JNI反调JAVA方法
        env->CallStaticVoidMethod(clazz, methodId, strArray);
    }
    
[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    JNIEnv* AndroidRuntime::getJNIEnv()
    {
        JNIEnv* env;
        JavaVM* vm = AndroidRuntime::getJavaVM();
        assert(vm != NULL);
        // 通过GetEnv可以通过JavaVM对象获得JNIEnv
        // 还有一种通过(*jvm)->AttachCurrentThread(jvm, (void**)&env, NULL)获取
        if (vm->GetEnv((void**) &env, JNI_VERSION_1_4) != JNI_OK)
            return NULL;
        return env;
    }

到这里就进入了Pm.java的main()函数，开始执行相应的操作。Pm.java中的操作最终都是通过PackageManagerService来完成的。

# 启动一个新进程中的Activity  

## 向zygote发送请求  

当需要打开的一个Activity属于一个新的进程时，是通过ActivityManagerService.java中的startProcessLocked()方法打开，它通过调用Process.java来启动一个新进程

[-> frameworks/base/core/java/android/os/Process.java]

    public static final ProcessStartResult start(final String processClass, final String niceName,
                                  int uid, int gid, int[] gids, int debugFlags, int mountExternal,
                                  int targetSdkVersion, String seInfo, String abi,
                                  String instructionSet, String appDataDir, String[] zygoteArgs)
    {
        // 这里的processClass = android.app.ActivityThread
        return startViaZygote(processClass, niceName, uid, gid, gids,
                    debugFlags, mountExternal, targetSdkVersion, seInfo,
                    abi, instructionSet, appDataDir, zygoteArgs);
    }
    
[-> frameworks/base/core/java/android/os/Process.java]

    private static ProcessStartResult startViaZygote(final String processClass,
                                  final String niceName, final int uid, final int gid,
                                  final int[] gids, int debugFlags, int mountExternal,
                                  int targetSdkVersion, String seInfo, String abi,
                                  String instructionSet, String appDataDir, String[] extraArgs)
    {
        // 设置很多进程的参数, 保存在argsForZygote里
        argsForZygote.add("--runtime-args");
        argsForZygote.add("--setuid=" + uid);
        argsForZygote.add("--setgid=" + gid);
        ... ...
        
        return zygoteSendArgsAndGetResult(openZygoteSocketIfNeeded(abi), argsForZygote);
    }
    
openZygoteSocketIfNeeded()方法就是打开zygote监听的socket套接字，通过它与zygote进行通信

[-> frameworks/base/core/java/android/os/Process.java]

    private static ZygoteState openZygoteSocketIfNeeded(String abi)
    {
        primaryZygoteState = ZygoteState.connect(ZYGOTE_SOCKET);
        
        if (primaryZygoteState.matches(abi)) {
            return primaryZygoteState;
        }
    }

其实就是新建一个ZygoteState对象，将它传给zygoteSendArgsAndGetResult()，它里面保存了与zygote进行socket通信的信息

[-> frameworks/base/core/java/android/os/Process.java]

    private static ProcessStartResult zygoteSendArgsAndGetResult(
            ZygoteState zygoteState, ArrayList<String> args)
            throws ZygoteStartFailedEx
    {
        final BufferedWriter writer = zygoteState.writer;
        final DataInputStream inputStream = zygoteState.inputStream;
        // 通过socket向zygote发送消息
        writer.write(Integer.toString(args.size()));
        writer.newLine();
        int sz = args.size();
        for (int i = 0; i < sz; i++) {
            String arg = args.get(i);
            if (arg.indexOf('\n') >= 0) {
                throw new ZygoteStartFailedEx(
                        "embedded newlines not allowed");
            }
            writer.write(arg);
            writer.newLine();
        }
        
        // 等待接受zygote返回的结果，就是新创建的进程的pid
        ProcessStartResult result = new ProcessStartResult();
        result.pid = inputStream.readInt();
    }
    
## zygote接收请求  

在上一篇中说过，zygote在启动完systemserver之后，就会进入循环等待socket消息然后处理消息。当有socket请求到来时，调用ZygoteConnection.java的runOnce()方法。后面的流程就和启动systemserver时差不多，只不过这次启动的是ActivityThread.java的main()方法。
