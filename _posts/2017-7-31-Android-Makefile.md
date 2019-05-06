---
layout: post
title:  "详解Android.mk"
subtitle: dacaoxin
author: dacaoxin
date:   2017-7-31 0:23:00
catalog:  true
tags:
    - rom
    - android
    - Makefile
---

## 1. 为什么是Android.mk

不知道有没有人想过这个问题，Android源码里为什么每个模块的编译文件为什么叫Android.mk, 而不是别的什么名字呢。这是因为在main.mk里明确指定了，以每个子目录下的Android.mk
这个文件作为模块编译的起始makfile文件。


[build/core/main.mk]

	subdir_makefiles := \
		$(shell build/tools/findleaves.py --prune=$(OUT_DIR) --prune=.repo --prune=.git $(subdirs) Android.mk)

	$(foreach mk, $(subdir_makefiles), $(info including $(mk) ...)$(eval include $(mk)))


所以在Android源码里，我们每次想看一个模块是如何编译的时候，总是把模块所在目录里的Android.mk作为编译的起始Makefile文件。


## 2. 如何阅读Android.mk


可能有朋友在琢磨是不是Android的编译系统重新定义了一套和GNU Makefile完全不同的规则？答案是否定的。其实在编译源码时，无论是直接使用make全编，还是使用mm\mmm命令全编译单个模块，
我们所遵循的原则和GNU Makefile是一模一样的，最终都是使用相同的make命令，所有GNU Makefile规则在Android源码里照样适用，只不过Android有着宠大并且复杂的编译系统为我们封装，让我
们可以更加清晰简便的做修改。


对于Android源码的build系统，比较复杂，涉及到的知识点也相对较多，这里只以Android.mk作为切入点，剩下的部分以后会有机会展开，由点及面，对build系统熟悉起来。


以Android源码里一个系统APP的Android.mk文件作为例子：


	LOCAL_PATH:= $(call my-dir)
	include $(CLEAR_VARS)

	LOCAL_MODULE_TAGS := optional

	LOCAL_SRC_FILES := $(call all-java-files-under, src) \
					src/com/android/music/IMediaPlaybackService.aidl

	LOCAL_PACKAGE_NAME := Music

	LOCAL_PROGUARD_FLAG_FILES := proguard.flags

	include $(BUILD_PACKAGE)


具体解释如下：
 

 * 每一个Androi.mk文件都必须以定义LOCAL_PATH变量开头，my-dir是由build系统定义的函数，作用是返回当前Android.mk在源码中目录
 * CLEAR_VARS是由build系统所定义的一个变量，它的值是build/core/clear_vars.mk，作用是清除很多LOCAL_开头的变量，但是不清理LOCAL_PATH，所以你可以当include $(CLEAR_VARS)这句
 作为每个模块编译的开始。
 * LOCAL_MODULE_TAGS用于定义当前模块在什么编译模式中被编译，它的值有eng, user, tests, optional。
 * LOCAL_PACKAGE_NAME变量指明了编译出apk的名字，只有当前模块是一个应用(APP)才使用LOCAL_PACKAGE_NAME; 其余情况下，无论是so或是jar包，全部都使用LOCAL_MODULE变量。
 * LOCAL_SRC_FILES变量指明编译使用的源码文件，all-java-files-under是由build系统定义的函数，作用是列出指定目录下所有的java文件。
 * LOCAL_PROGUARD_FLAG_FILES指定混淆文件，上例中表明当前目录下proguard.flags作为混淆文件。
 * BUILD_PACKAGE也是由build系统定义的一个变量，它的值是build/core/package.mk, 表示编译出一个apk文件。一般来讲，类似include $(BUILD_PACKAGE)可以作为一个模块编译的结束。
 

和BUILD_PACKAGE变量类似的还有好几个，这里列出其中常见的一部分：
 

 * BUILD_JAVA_LIBRARY  --  build/core/java_library.mk; 表示编译一个jar包, 里面是DEX格式的文件
 * BUILD_STATIC_JAVA_LIBRARY – build/core/static_java_library.mk; 也编译一个jar包，但是里面每个java文件所对应的class文件都存在
 * BUILD_EXECUTABLE  -- build/core/executable.mk; 编译一个可执行的bin程序
 * BUILD_PREBUILT  -- build/core/prebuilt.mk；用于集成第三方的jar包或者so库等
 

## 3. 常见变量
 

* LOCAL_STATIC_JAVA_LIBRARIES/LOCAL_JAVA_LIBRARIES - 指明编译当前模块所依赖的jar包
* LOCAL_CERTIFICATE := platform - 指明使用platform key来对当前模块进行签名
* LOCAL_AAPT_FLAGS - Android源码里使用aapt打包jar包或者apk文件，这个变量可以定义aapt打包参数，比如 ：--auto-add-overlay， --extra-packages
* LOCAL_PROGUARD_ENABLED - 是否进行混淆


## 4. 调试手段


我们调试代码的时候，最常用的手段就是打log, 在不明白的地方，或者不知道走了哪个if分支，或者想看看变量的值是什么，都可以打log看。

Android build系统里也可以打Log，使用的函数是warning / info / error。
 

> 需要注意的是，error函数会让编译直接停下来，所以一般warning和info更常用一点
 

使用示例(以warning为例，其它两个类似)：
 

* 打印普通字符串(hello world)：


	$(warning hello world)	


* 打印变量的值：


	$(warning $LOCAL_PACKAGE_NAME)


* 变量和字符串组合打印:


	$(warning this apk is $LOCAL_PACKAGE_NAME)
