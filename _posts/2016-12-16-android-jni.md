---
layout: post
title:  "Android jni技术"
subtitle: dacaoxin
author: dacaoxin
date:   2016-12-16 21:12:50
catalog:  true
tags:
    - android
    - jni
    - native
---
# Android JNI学习笔记

## java层加载JNI库
java层类调用jni代码一般会有一个静态代码块，静态代码块中使用System.loadLibrary加载so库。

    public class MediaPlayer {
        static {
            System.loadLibrary("media_jni");
            // 调用jni的init函数
            native_init();
        }
    }
    
    private static native final void native_init();
    
使用native关键字修饰的native_init()函数是一个native函数，具体实现由JNI代码完成。

> 目前还不清楚为什么同一个jni库可以被load多次

## JNI层的实现
* 静态注册JNI  
javah生成对应的JNI头文件，然后写一个cpp文件来实现头文件中的函数即可。静态注册的JNI函数名字是需要有特定的命令规则的，java代码就是依靠这个命令才可以找到对应的JNI函数，静态注册JNI不是我们这里要讨论的重点。

* 动态注册JNI

静态注册会有一个缺点，就是第一次调用某个jni函数时，都需要根据名字来搜索并建立对应关系，这样的效率会觉得比较低。由此便有了动态注册，所谓动态注册，就是通过某个变量来记录java方法和jni函数的对应关系。

即便动态注册JNI并不要求java层方法和native函数的名字要有一定的关系，但是android里为了代码的可读性更高，仍然使它们之间有一定的关系。比如MediaPlayer.java所在的包名是android.media, 所以它里的native_init()方法，它对应的JNI函数在：
[->android_media_MediaPlayer.cpp]

    static void android_media_MediaPlayer_native_init(JNIEnv *env)

文件名“是包名+java文件名.cpp”， 函数名是“包名+java文件名+函数名”，然后把‘.’换成‘_’。

还有另外一种方式也可以找到java方法对应的JNI函数的实现。以MediaPlayer.java代码为例，在android源代码里，一定可以在一个Android.mk中找到libmedia_jni这样的LOCAL_MODULE，这个Android.mk所在的目录就是so库所对应的JNI代码。  
[->framework/base/media/jni/Android.mk]

    LOCAL_MODULE := libmedia_jni

函数JNI_OnLoad就是这个so库的入口，在JNI_OnLoad函数里对Java函数和JNI函数建立链接，方便以后调用.

[->framework/base/media/jni/android_media_MediaPlayer.cpp]

    jint JNI_OnLoad(JavaVM* vm, void* /* reserved */)
    {
        JNIEnv* env = NULL;
        jint result = -1;
    
        if (vm->GetEnv((void**) &env, JNI_VERSION_1_4) != JNI_OK) {
            ALOGE("ERROR: GetEnv failed\n");
            goto bail;
        }
        assert(env != NULL);
    
        if (register_android_media_ImageReader(env) < 0) {
            ALOGE("ERROR: ImageReader native registration failed");
            goto bail;
        }
        
        // 这个函数里就是建立MediaPlayer.java中方法与JNI函数的联系
        if (register_android_media_MediaPlayer(env) < 0) {
            ALOGE("ERROR: MediaPlayer native registration failed\n");
            goto bail;
        }
        ...
    }
    
[->framework/base/media/jni/android_media_MediaPlayer.cpp]

    static JNINativeMethod gMethods[] = {
        {
            "nativeSetDataSource",
            "(Landroid/os/IBinder;Ljava/lang/String;[Ljava/lang/String;"
            "[Ljava/lang/String;)V",
            (void *)android_media_MediaPlayer_setDataSourceAndHeaders
        },
        {"_setDataSource",       "(Ljava/io/FileDescriptor;JJ)V",    (void *)android_media_MediaPlayer_setDataSourceFD},
        {"_setVideoSurface",    "(Landroid/view/Surface;)V",        (void *)android_media_MediaPlayer_setVideoSurface},
        {"_prepare",            "()V",                              (void *)android_media_MediaPlayer_prepare},
        {"prepareAsync",        "()V",                              (void *)android_media_MediaPlayer_prepareAsync},
        {"_start",              "()V",                              (void *)android_media_MediaPlayer_start},
        {"_stop",               "()V",                              (void *)android_media_MediaPlayer_stop},
        {"getVideoWidth",       "()I",                              (void *)android_media_MediaPlayer_getVideoWidth},
        {"getVideoHeight",      "()I",                              (void *)android_media_MediaPlayer_getVideoHeight},
        {"seekTo",              "(I)V",                             (void *)android_media_MediaPlayer_seekTo},
        {"_pause",              "()V",                              (void *)android_media_MediaPlayer_pause},
        {"isPlaying",           "()Z",                              (void *)android_media_MediaPlayer_isPlaying},
        {"getCurrentPosition",  "()I",                              (void *)android_media_MediaPlayer_getCurrentPosition},
        {"getDuration",         "()I",                              (void *)android_media_MediaPlayer_getDuration},
        {"_release",            "()V",                              (void *)android_media_MediaPlayer_release},
        {"_reset",              "()V",                              (void *)android_media_MediaPlayer_reset},
        {"_setAudioStreamType", "(I)V",                             (void *)android_media_MediaPlayer_setAudioStreamType},
        {"_getAudioStreamType", "()I",                              (void *)android_media_MediaPlayer_getAudioStreamType},
        {"setParameter",        "(ILandroid/os/Parcel;)Z",          (void *)android_media_MediaPlayer_setParameter},
        {"setLooping",          "(Z)V",                             (void *)android_media_MediaPlayer_setLooping},
        {"isLooping",           "()Z",                              (void *)android_media_MediaPlayer_isLooping},
        {"_setVolume",          "(FF)V",                            (void *)android_media_MediaPlayer_setVolume},
        {"native_invoke",       "(Landroid/os/Parcel;Landroid/os/Parcel;)I",(void *)android_media_MediaPlayer_invoke},
        {"native_setMetadataFilter", "(Landroid/os/Parcel;)I",      (void *)android_media_MediaPlayer_setMetadataFilter},
        {"native_getMetadata", "(ZZLandroid/os/Parcel;)Z",          (void *)android_media_MediaPlayer_getMetadata},
        {"native_init",         "()V",                              (void *)android_media_MediaPlayer_native_init},
        {"native_setup",        "(Ljava/lang/Object;)V",            (void *)android_media_MediaPlayer_native_setup},
        {"native_finalize",     "()V",                              (void *)android_media_MediaPlayer_native_finalize},
        {"getAudioSessionId",   "()I",                              (void *)android_media_MediaPlayer_get_audio_session_id},
        {"setAudioSessionId",   "(I)V",                             (void *)android_media_MediaPlayer_set_audio_session_id},
        {"_setAuxEffectSendLevel", "(F)V",                          (void *)android_media_MediaPlayer_setAuxEffectSendLevel},
        {"attachAuxEffect",     "(I)V",                             (void *)android_media_MediaPlayer_attachAuxEffect},
        {"native_pullBatteryData", "(Landroid/os/Parcel;)I",        (void *)android_media_MediaPlayer_pullBatteryData},
        {"native_setRetransmitEndpoint", "(Ljava/lang/String;I)I",  (void *)android_media_MediaPlayer_setRetransmitEndpoint},
        {"setNextMediaPlayer",  "(Landroid/media/MediaPlayer;)V",   (void *)android_media_MediaPlayer_setNextMediaPlayer},
    };

    static int register_android_media_MediaPlayer(JNIEnv *env)
    {
        return AndroidRuntime::registerNativeMethods(env,
                    "android/media/MediaPlayer", gMethods, NELEM(gMethods));
    }

AndroidRuntime.cpp里的className字符串，是为了标识这个JNINativeMethod是属于哪个JAVA类的。    
[->AndroidRuntime.cpp]

    int AndroidRuntime::registerNativeMethods(JNIEnv* env,
  
    const char* className, const JNINativeMethod* gMethods, int numMethods)
    {
        return jniRegisterNativeMethods(env, className, gMethods, numMethods);
    }
    
* jni函数所有参数的意义


    android_media_MediaScanner_processFile(JNIEnv*env, jobject thiz,
        jstring path, jstring mimeType, jobject client)    
jobject thiz代表的是调用JNI的JAVA侧的对象，如果java层是static函数的话，这个参数变为jclass, 代表的是调用JNI的java类。
后面我们重点说一下JNIEnv *env这个参数。

# JavaVM与JNIEnv  
JNI定义了两个重要的数据结构，JavaVM和JNIEnv。JavaVM是JAVA虚拟机在JNI层的代表。理论上，JAVA的每个进程里允许有多个JavaVM,但是android里只允许存在一个。
JNIEnv可以看作JavaVM在线程中的代表，每个线程只有一个，JNIEnv提供了大部分的JNI函数，基本上每个native函数的第一个参数都是JNIEnv.因为JNIEnv只与当前线程相关，所以GOOGLE建议不要在线程之前共享JNIEnv，也不要保存JNIEnv, 如果一个线程无法获取到它的JNIEnv时，可以由以下两个函数通过JavaVM获取：

    jint AttachCurrentThread(JNIEnv **penv, void *args)
    GetEnv((void **), int)


* JAVA层与JNI层基本数据类型转换 

|java类型     |    native类型   |
|:-----------:|:---------------:|
|boolean      | jboolean        |
|byte         | jbyte           |
|char         | jchar           |
|short        | jshort          |
|int          | jint            |
|long         | jlong           |
|float        | jfloat          |
|double       | jdouble         |

* JAVA层与JNI层引用数据类型转换

|java类型     |    native类型   |java类型     |    native类型   |
|:-----------:|:---------------:|:-----------:|:---------------:|
|All objects  | jobject         | char[]      | jcharArray      |
|Class        | jclass          | short[]     | jshortArray     |
|String       | jstring         | int[]       | jintArray       |
|Object[]     | jobjectArray    | long[]      | jlongArray      |
|boolean[]    | jbooleanArray   | float[]     | jfloatArray     |
|byte[]       | jbyteArray      | double[]    | jdoubleArray    |
|Throwable    | jthrowable      |
除了java基本类型和基本类型数组以及class, string, throwable以外，其余的所有类型在native层全部用jobject来表示。

* java方法与native方法的融合剂JNINativeMethod


    typedef struct {  
        char *name;  
        char *signature;  
        void *fnPtr;  
    } JNINativeMethod
    
name是java层方法的名字，fnPtr是jni层与java层方法对应的函数指针，这里我们重点说一下signature，从字面上看，它叫做签名。它是由jni函数的输入参数和返回参数类型共同组成的，它的作用就是为了蔽免因为java侧函数的重载而无法在jni层找到对应的函数。具体格式规则如下：

> (参数1类型标示参数2类型标示...参数n类型标示)返回值类型标示

