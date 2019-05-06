---
layout: post
title:  "Zygote分析(一)"
subtitle: dacaoxin
author: dacaoxin
date:   2016-12-1 20:10:00
catalog:  true
tags:
    - android
    - framework
    - native
    - zygote
---

## zygote介绍    
  zygote单词的意思是"受精卵"的意思，它的作用就像它的名字一样。实际上它就是android java世界的先祖，所有的JAVA进程，所括APP进程都是通过zygote启动起来的。
  
  我们在开发android的过程中，经常会遇到系统重启的问题，其实你去看logcat的时候，都会发现一定是什么原因最终导致zygote关闭了。其实我也是一直都听说过zygote很重要，但是它倒底做了些什么事情呢？在这里通过源代码的方法分析一下:


## zygote启动脚本    

zygote本质上也是一个进程，由于android其实是基于linux内核的，所以实际上zygote就是一个linux的应用程序。它必然是通过init进程启动的，一般可以在源码的system/目录下找到zygote的启动脚本:

[-> system/core/rootdir/init.zygote64_32.rc]

    service zygote /system/bin/app_process64 -Xzygote /system/bin --zygote --start-system-server --socket-name=zygote
        class main
        socket zygote stream 660 root system
        onrestart write /sys/android_power/request_state wake
        onrestart write /sys/power/state on
        onrestart restart media
        onrestart restart netd

## zygote进程源码分析  

可执行程序app_process64的代码就是app_main.cpp    

[-> framework/base/cmds/app_process/App_main.cpp]

    int main(int argc, char* const argv[])
    {
        AppRuntime runtime(argv[0], computeArgBlockSize(argc, argv));
        argc--;
        argv++;
        
        int i;
        for (i = 0; i < argc; i++) {
            if (argv[i][0] != '-') {
                break;
            }
            if (argv[i][1] == '-' && argv[i][2] == 0) {
                ++i; // Skip --.
                break;
            }
            // 这里会传入两个参数: argv[0] = -Xzygote; argv[1] = /system/bin
            runtime.addOption(strdup(argv[i]));
        }
        
        // Parse runtime arguments.  Stop at first unrecognized option.
        bool zygote = false;
        bool startSystemServer = false;
        bool application = false;
        String8 niceName;
        String8 className;
    
        ++i;  // Skip unused "parent dir" argument.
        while (i < argc) {
            const char* arg = argv[i++];
    		ALOGD("i = %d, arg = %s", i,  arg);
            if (strcmp(arg, "--zygote") == 0) {     // 启动脚本传入的有--zygote参数
                zygote = true;
                niceName = ZYGOTE_NICE_NAME;
            } else if (strcmp(arg, "--start-system-server") == 0) {     // 启动脚本传入的有--start-system-server参数
                startSystemServer = true;
            } else if (strcmp(arg, "--application") == 0) {
                application = true;
            } else if (strncmp(arg, "--nice-name=", 12) == 0) {
                niceName.setTo(arg + 12);
            } else if (strncmp(arg, "--", 2) != 0) {
                className.setTo(arg);
                break;
            } else {
                --i;
                break;
            }
        }
        
        Vector<String8> args;
        if (!className.isEmpty()) {     //  这里的className是空的，所以走else
            // We're not in zygote mode, the only argument we need to pass
            // to RuntimeInit is the application argument.
            //
            // The Remainder of args get passed to startup class main(). Make
            // copies of them before we overwrite them with the process name.
            args.add(application ? String8("application") : String8("tool"));
            runtime.setClassNameAndArgs(className, argc - i, argv + i);
        } else {
            // We're in zygote mode.
            maybeCreateDalvikCache();
    
            if (startSystemServer) {        // 有--start-system-server参数，所以startSystemServer为true
                // 为args追加一个"start-system-server"
                args.add(String8("start-system-server"));
            }
    
            char prop[PROP_VALUE_MAX];
            if (property_get(ABI_LIST_PROPERTY, prop, NULL) == 0) {
                LOG_ALWAYS_FATAL("app_process: Unable to determine ABI list from property %s.",
                    ABI_LIST_PROPERTY);
                return 11;
            }
    
            String8 abiFlag("--abi-list=");
            abiFlag.append(prop);
            args.add(abiFlag);
    
            // 把init里zygote启动脚本里剩余的参数同时放入args
            for (; i < argc; ++i) {
                args.add(String8(argv[i]));
            }
        }
    
        if (!niceName.isEmpty()) {      //  niceName = zygote
            runtime.setArgv0(niceName.string());
            // 通过linux的prctl系统调用，更改进程的名字为"zygote"
            set_process_name(niceName.string());
        }
    
        if (zygote) {       // zygote = true, 这里调用AppRuntime的start()方法
            runtime.start("com.android.internal.os.ZygoteInit", args, zygote);
        } else if (className) {
            runtime.start("com.android.internal.os.RuntimeInit", args, zygote);
        } else {
            fprintf(stderr, "Error: no class name or --zygote supplied.\n");
            app_usage();
            LOG_ALWAYS_FATAL("app_process: no class name or --zygote supplied.");
            return 10;
        }
    }
    
到这里，app_main就分析完了，总结一下：
1. app_main分析了init里的zygote启动脚本，解析它的启动参数。
2. 把app_process进程的名字改为"zygote"
3. 根据传入的参数有"--zygote"然后调用AppRuntime的start()函数
4. 传入start的参数args里的字符串为: start-system-server; --abi-list=arm64-v8a; --socket-name=zygote; 第三个参数zygote = true

因为AppRuntime是继承于AndroidRuntime, 所以start()的实现为：  
[-> framework/base/core/jni/AndroidRuntime.cpp]  

    void AndroidRuntime::start(const char* className, const Vector<String8>& options, bool zygote)
    {
        // 设置环境变量"ANDROID_ROOT"的值为: /system
        setenv("ANDROID_ROOT", "/system", 1);
        startVm(&mJavaVM, &env, zygote);        // 创建JAVA虚拟机
        startReg(env);      // 注册JNI函数
        
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
        // 上面这一串代码就是在strArray中放入：com.android.internal.os.ZygoteInit; start-system-server; 
        //                                     --abi-list=arm64-v8a; --socket-name=zygote
        
        // toSlashClassName的作用就是把com.android.internal.os.ZygoteInit中的'.'换成符合JNI规则的'/'
        char* slashClassName = toSlashClassName(className);
        jclass startClass = env->FindClass(slashClassName);
        jmethodID startMeth = env->GetStaticMethodID(startClass, "main", "([Ljava/lang/String;)V");
        
        // 通过JNI调用ZygoteInit.java中的main()方法
        env->CallStaticVoidMethod(startClass, startMeth, strArray);
    }

总结一下，start()函数主要做的工作如下：
1. 创建JAVA虚拟机，为运行JAVA代码准备条件，并且注册了JNI函数，方便JAVA调用本地方法
2. 通过JNI反调ZygoteInit.java的main()方法，并传入字符串数组作为参数：com.android.internal.os.ZygoteInit; start-system-server; 
                                                                --abi-list=arm64-v8a; --socket-name=zygote

现在回过头来看看startVm()和startReg()里具体都干了些什么

[-> frameworks/base/core/jni/AndroidRuntime.cpp]    

    int AndroidRuntime::startVm(JavaVM** pJavaVM, JNIEnv** pEnv, bool zygote)
    {
        ... ...
        // 设置JAVA虚拟机的参数，包括堆栈大小，是否进行JNI检测
        parseRuntimeOption("dalvik.vm.heapstartsize", heapstartsizeOptsBuf, "-Xms", "4m");
        parseRuntimeOption("dalvik.vm.heapsize", heapsizeOptsBuf, "-Xmx", "16m");
        ... ...
        initArgs.version = JNI_VERSION_1_4;
        initArgs.options = mOptions.editArray();
        initArgs.nOptions = mOptions.size();
        initArgs.ignoreUnrecognized = JNI_FALSE;
        
        JNI_CreateJavaVM(pJavaVM, pEnv, &initArgs)
    }

startVm()函数非常长，不过功能比较清晰，就是设置JAVA虚拟机的参数，并且启动虚拟机。其中很多参数是在MAKEFILE中通过property定义的。

[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    int AndroidRuntime::startReg(JNIEnv* env)
    {
        androidSetCreateThreadFunc((android_create_thread_fn) javaCreateThreadEtc);
        
        register_jni_procs(gRegJNI, NELEM(gRegJNI), env)
    }

register_jni_procs()这里会注册很多JNI方法。接着看看androidSetCreateThreadFunc()里干了什么。

[-> system/core/libutils/Threads.cpp]  

    void androidSetCreateThreadFunc(android_create_thread_fn func)
    {
        gCreateThreadFn = func;
    }
    
熟悉Android c++ Thread的话，就知道函数指针gCreateThreadFn就是线程循环的入口函数，在这里相当于重新定义了c++线程的入口函数，那么所有在这个进程中创建出来的线程，都将使用这个函数作为入口, 接着看看javaCreateThreadEtc()这个函数有什么特殊的地方：

[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    int AndroidRuntime::javaCreateThreadEtc(
                                android_thread_func_t entryFunction,
                                void* userData,
                                const char* threadName,
                                int32_t threadPriority,
                                size_t threadStackSize,
                                android_thread_id_t* threadId)
    {
        args[0] = (void*) entryFunction;
        args[1] = userData;
        args[2] = (void*) strdup(threadName);   // javaThreadShell must free
    
        result = androidCreateRawThreadEtc(AndroidRuntime::javaThreadShell, args,
            threadName, threadPriority, threadStackSize, threadId);
    }

[-> system/core/libutils/Threads.cpp]

    int androidCreateRawThreadEtc(android_thread_func_t entryFunction,
                                   void *userData,
                                   const char* threadName __android_unused,
                                   int32_t threadPriority,
                                   size_t threadStackSize,
                                   android_thread_id_t *threadId)
    {
        int result = pthread_create(&thread, &attr,
                    (android_pthread_entry)entryFunction, userData);
    }
    
[-> frameworks/base/core/jni/AndroidRuntime.cpp]

    int AndroidRuntime::javaThreadShell(void* args) 
    {
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

可以看出，javaThreadShell()作为线程的运行函数，然后在javaThreadShell()里又调用了javaCreateThreadEtc()里的第一个参数作为真正的线程运行函数。

到这里为止，zygote的cpp代码差不多分析完了。接下来就是调用ZygoteInit.java的main()方法进入JAVA的世界。
