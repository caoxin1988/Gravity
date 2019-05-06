---
layout: post
title:  "dumpsys原理"
subtitle: dacaoxin
author: dacaoxin
date:   2017-8-4 0::00
catalog:  true
tags:
    - rom
    - android
    - framework
---

> warning: 这篇文章只是盏指路灯，而不是你想要的一切，如果你想有更深入的了解，请参考本文自己阅读源代码

dumpsys命令是Android系统自带的一个非常强大的用于我们平时debug问题时的命令，用它可以dump出很多很重要的当前系统服务相关的信息，而这些信息又
在我们调试问题时显得非常重要，比如我就特别喜欢用dumpsys activity activities命令帮助我查看activity栈和task栈的信息。

今天我们就来一起看看dumpsys是怎么做到这些屌炸天的事情的。

## 1. dumpsys命令的实现

先通过源码简单说下dumpsys的实现原理，dumpsys命令的源码位于frameworks/native/cmds/dumpsys/目录下, 先看下它的主Makefile文件


	LOCAL_PATH:= $(call my-dir)
	include $(CLEAR_VARS)

	LOCAL_SRC_FILES:= \
		dumpsys.cpp

		... ...

	LOCAL_MODULE:= dumpsys

	include $(BUILD_EXECUTABLE)


从Makefile文件可以看出来，dumpsys的源码只有当前目录下的dumpsys.cpp这一个文件。

frameworks/native/cmds/dumpsys/dumpsys.cpp


	int main(int argc, char* const argv[]) {

		sp<IServiceManager> sm = defaultServiceManager();
		
		Vector<String16> services;
	    Vector<String16> args;
		bool showListOnly = false;
		// "dumpsys -l"命令
	    if ((argc == 2) && (strcmp(argv[1], "-l") == 0)) {
	        showListOnly = true;
	    }
		// "dumpsys"命令
	    if ((argc == 1) || showListOnly) {
	        services = sm->listServices();
	        services.sort(sort_func);
	        args.add(String16("-a"));
	    } else {
		// "dumpsys xxx "具体到某一个service
	        services.add(String16(argv[1]));
	        for (int i=2; i<argc; i++) {
	            args.add(String16(argv[i]));
	        }
	    }

		for (size_t i=0; i<N; i++) {
			// 通过servicemanager找到注册的service
	        sp<IBinder> service = sm->checkService(services[i]);
	        if (service != NULL) {
				// 调用相关service的dump方法，这是dumpsys的核心
	            int err = service->dump(STDOUT_FILENO, args);
	        }
	    }
	}


如果你不想仔细看dumpsys.cpp的源代码，那我告诉你一些结论：

* "dumpsys -l"命令列出当前系统中所有可以dump的系统服务信息
* 使用dumpsys时，它先通过service_manager拿到需要的系统服务的远端代理对象，然后再使用这个远端代理，通过binder机制，调用service的dump()方法
* 如果只输入"dumpsys", 那么它会把所有系统服务可dump的信息，全部dump出来

## 2. AMS作为例子

我们以AMS(ActivityManagerService)作为一个实例，来看看dumpsys是如何工作的。

SystemServer进程在启动完AMS之后，会调用AMS的setSystemProcess()方法：


	public void setSystemProcess() {
		// Context.ACTIVITY_SERVICE = "activity"
		ServiceManager.addService(Context.ACTIVITY_SERVICE, this, true);
		ServiceManager.addService(ProcessStats.SERVICE_NAME, mProcessStats);
		ServiceManager.addService("meminfo", new MemBinder(this));
		ServiceManager.addService("gfxinfo", new GraphicsBinder(this));
		ServiceManager.addService("dbinfo", new DbBinder(this));
		ServiceManager.addService("permission", new PermissionController(this));
		
		... ...
	}


这个方法向service_manager注册几个系统服务，其中就有一个名字叫"activity"的服务，也就是AMS自己。当使用"dumpsys activity"命令的时候，就会调用AMS的
dump()方法。


	protected void dump(FileDescriptor fd, PrintWriter pw, String[] args) {
		... ... 
		
		if ("activities".equals(cmd) || "a".equals(cmd)) {
			dumpActivitiesLocked(fd, pw, args, opti, true, dumpClient, null);
		} else if ("recents".equals(cmd) || "r".equals(cmd)) {
			dumpRecentsLocked(fd, pw, args, opti, true, null);
		} else if ("broadcasts".equals(cmd) || "b".equals(cmd)) {
			dumpBroadcastsLocked(fd, pw, args, opti, true, name);
		} else
			... ...
		
		... ...
	}


代码逻辑比较简单，最终对"dumpsys activity"的实现全部在这里，这里可以根据传入的参数不同，dump出所有AMS控制的信息，比如activity栈，service, broadcast等等。

## 3. 常用的dumpsys服务

dumpsys虽然可以dump出来的系统信息非常多，但是有很多可能并不是那么常见，这里列出一些经常会dump的一些系统服务，感兴趣可以自行查看源代码看看具体实现在哪些功能。

|  服务名  |  类名 |   功能 |
|----------|--------|----------|
|activity|ActivityManagerService|AMS相关信息|
|package|PackageManagerService|PKMS相关信息|
|window|WindowManagerService|WMS相关信息|
|input|InputManagerService|IMS相关信息|
|power|PowerManagerService|PMS相关信息|
|procstats|ProcessStatsService|进程统计|
|battery|BatteryService|电池信息|
|meminfo|MemBinder|内存信息|

总之dumpsys命令十分的强大，这里只是简单介绍了一下dumpsys的实现原理，至于使用dumpsys命令的真实安例，后续会再分享。