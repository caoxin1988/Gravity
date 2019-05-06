---
layout: post
title:  "Watchdog原理分析"
subtitle: dacaoxin
author: dacaoxin
date:   2017-8-27 9:51
catalog:  true
tags:
    - rom
    - android
    - framework
---


## 1. Watchdog启动

上一篇文章简单介绍了Watchdog 的定义，并用一个实例介绍Watchdog引起系统重启的问题分析，让大家对Watchdog有了一个感性的认识。本文旨在介绍Watchdog的工作原理，让大家有一个理性认识。

首先帮大家理一下Watchdog主要成员的类继承关系：

![watchdog class](/images/watchdog/watchdog_class.png)

Watchdog继承于Thread, 它实际上是运行在system_server进程里的一个线程，它的启动代码：

[frameworks/base/services/java/com/android/server/SystemServer.java]

	private void startOtherServices() {
		... ...
		
		final Watchdog watchdog = Watchdog.getInstance();
        watchdog.init(context, mActivityManagerService);
		
		mActivityManagerService.systemReady(new Runnable() {
            @Override
            public void run() {
				... ...
				// Watchdog线程正式启动起来
				Watchdog.getInstance().start();
				
				... ...
			}
		}
		
		... ...
	}

* Watchdog类的实现采用了java中常用的单例模式。在getInstance()方法中构造类对象。
* Android系统启动完成后会调用mActivityManagerService.systemReady()方法，在这个方法里通过start()让Watchdog线程开始工作。

Watchdog构造方法:

[frameworks/base/services/core/java/com/android/server/Watchdog.java]

	private Watchdog() {
		mMonitorChecker = new HandlerChecker(FgThread.getHandler(),
                "foreground thread", DEFAULT_TIMEOUT);
        mHandlerCheckers.add(mMonitorChecker);

        mHandlerCheckers.add(new HandlerChecker(new Handler(Looper.getMainLooper()),
                "main thread", DEFAULT_TIMEOUT));

        mHandlerCheckers.add(new HandlerChecker(UiThread.getHandler(),
                "ui thread", DEFAULT_TIMEOUT));

        mHandlerCheckers.add(new HandlerChecker(IoThread.getHandler(),
                "i/o thread", DEFAULT_TIMEOUT));

        mHandlerCheckers.add(new HandlerChecker(DisplayThread.getHandler(),
                "display thread", DEFAULT_TIMEOUT));

        addMonitor(new BinderThreadMonitor());
	}
	
## 2. Watchdog工作原理

先看一下Watchdog的总体框图:

![watchdog diagram](/images/watchdog/watchdog_thread.png)

* FgThread，UiThread, IoThread, DisplayThread是Android系统中实现的特殊线程，从名字大概就可以看出它们的作用
* Looper.getMainLooper()其实就是system_server这个进程的main looper, 因为SystemServer.java里有调用Looper.prepareMainLooper()
* 实际上被Watchdog直接监测的是上面这5个线程的looper是否正常, 当然还会通过addThread()添加需要被监测的looper
* FgThread线程的looper又负责监测重要的系统服务是否死锁，比如AMS, PMS，...

我们以AMS为例，看看Watchdog是如何监测它是否死锁的，先看ActivityManagerService.java类做了哪些特殊处理：

[frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java]

	public final class ActivityManagerService extends ActivityManagerNative
        implements Watchdog.Monitor, BatteryStatsImpl.BatteryCallback {
		... ...
		
		public ActivityManagerService(Context systemContext) {
			... ...
			
			Watchdog.getInstance().addMonitor(this);
			Watchdog.getInstance().addThread(mHandler);
			
			... ...
		}
		
		public void monitor() {
			synchronized (this) { }
		}
		
		... ...
	}

* AMS要继承Watchdog.Monitor这个接口
* AMS里要实现Watchdog.Monitor接口的monitor()方法，只需要实现一个持锁操作就可以了
* 通过addMonitor()方法，将AMS添加到mMonitorChecker这个HandlerChecker类对象里

Android系统启动完成后，Watchdog线程开始运行，进入Watchdog.java的run()方法。

[frameworks/base/services/core/java/com/android/server/Watchdog.java]

	public void run() {

		while(true) {
		
			long timeout = CHECK_INTERVAL;
		
			for (int i=0; i<mHandlerCheckers.size(); i++) {
				HandlerChecker hc = mHandlerCheckers.get(i);
				hc.scheduleCheckLocked();
			}
			
			while (timeout > 0) {
				wait(timeout);
			}
			
			final int waitState = evaluateCheckerCompletionLocked();

			if (waitState == COMPLETED) {
				waitedHalf = false;
				continue;
			} else if (waitState == WAITING) {
				continue;
			} else if (waitState == WAITED_HALF) {
				if (!waitedHalf) {
					ArrayList<Integer> pids = new ArrayList<Integer>();
					pids.add(Process.myPid());
					ActivityManagerService.dumpStackTraces(true, pids, null, null,
							NATIVE_STACKS_OF_INTEREST);
					waitedHalf = true;
				}
				continue;
			}
			
			blockedCheckers = getBlockedCheckersLocked();
			subject = describeCheckersLocked(blockedCheckers);
			
			 if (debuggerWasConnected >= 2) {
                Slog.w(TAG, "Debugger connected: Watchdog is *not* killing the system process");
            } else if (debuggerWasConnected > 0) {
                Slog.w(TAG, "Debugger was connected: Watchdog is *not* killing the system process");
            } else if (!allowRestart) {
                Slog.w(TAG, "Restart not allowed: Watchdog is *not* killing the system process");
            } else {
				Process.killProcess(Process.myPid());
			}
		}
	}
	
* 在Watchdog线程的run()方法里，先逐一调用mHandlerCheckers里的每一个HandlerChecker对象的scheduleCheckLocked()方法做一次试探操作，当然包括mMonitorChecker
* 等待CHECK_INTERVAL时间(CHECK_INTERVAL是真正TIMEOUT时间的一半), 然后调用evaluateCheckerCompletionLocked()方法查看试探操作之后的结果，这里返回的结果是所有HandlerChecker对象结果中最滞后的值
* 如果试探结果是WAITED_HALF，就会调用ActivityManagerService.dumpStackTraces()打印堆栈到trace文件，然后接着再进行一次试探操作
* 如果在第二个CHECK_INTERVAL时间后返回值是OVERDUE，则通过getBlockedCheckersLocked()和describeCheckersLocked()方法获取被block的looper和monitor信息，然后通过Process.killProcess(Process.myPid())杀死system_server进程

### 2.1 hc.scheduleCheckLocked()

    public void scheduleCheckLocked() {
		if (mMonitors.size() == 0 && mHandler.getLooper().getQueue().isPolling()) {
			mCompleted = true;
			return;
		}

		if (!mCompleted) {
			return;
		}

		mCompleted = false;
		mCurrentMonitor = null;
		mStartTime = SystemClock.uptimeMillis();
		mHandler.postAtFrontOfQueue(this);
	}
	
AMS作为monitor对象存在于mMonitorChecker对象中，所以在试探操作时会调用mHandler.postAtFrontOfQueue(this)方法，等待执行mMonitorChecker的run()方法。

	public void run() {
		final int size = mMonitors.size();
		for (int i = 0 ; i < size ; i++) {
			synchronized (Watchdog.this) {
				mCurrentMonitor = mMonitors.get(i);
			}
			mCurrentMonitor.monitor();
		}

		synchronized (Watchdog.this) {
			mCompleted = true;
			mCurrentMonitor = null;
		}
	}
	
mMonitors里有一项就是AMS，所以在run()方法里会调用AMS的monitor, 还记得前面说过吗，AMS的monitor()方法就是一个等等持锁操作 synchronized (this) { }, 如果AMS有死锁发生，run()方法就无法往下执行，mCompleted也无法为true.

这里还有一种情况，就是上面说的，Watchdog除了监测mMonitorChecker代表的looper外，还有其它的一些线程looper, 这些looper里是没有monitor的(Android系统中所有的monitor全在mMonitorChecker中)。那对于这些looper, 看这两段代码
可以看到，对它们的试探操作主要是通过看looper的queue是否有阻塞来判断的，如果queue有阻塞，上面的run()方法一定无法执行到。

### 2.2 evaluateCheckerCompletionLocked()

	private int evaluateCheckerCompletionLocked() {
        int state = COMPLETED;
        for (int i=0; i<mHandlerCheckers.size(); i++) {
            HandlerChecker hc = mHandlerCheckers.get(i);
            state = Math.max(state, hc.getCompletionStateLocked());
        }
        return state;
    }
	
evaluateCheckerCompletionLocked()方法的返回值，是mHandlerCheckers集合中所有HandlerChecker对象中最滞后的状态值。

	public int getCompletionStateLocked() {
		if (mCompleted) {
			return COMPLETED;
		} else {
			long latency = SystemClock.uptimeMillis() - mStartTime;
			if (latency < mWaitMax/2) {
				return WAITING;
			} else if (latency < mWaitMax) {
				return WAITED_HALF;
			}
		}
		return OVERDUE;
	}
	
通过判断mCompleted的值并结合HandlerChecker的等待时间来决定HandlerChecker对象当前的状态值。

### 2.3 超时之后

Watchdog默认的超时时间是1分钟，如果有死锁或阻塞发生超过1分钟，Watchdog就会认为超时。这时一般会直接杀死system_server, 但是有两种情况并不会重启

1. debuggerWasConnected > 0, 也就是连接了调试器，系统正在被调试
2. allowRestart = false, 可以通过am hang命令更改这个值

## 3. 小结

本文通过源码介绍Watchdog的实现原理，具体总结如下：

1. Watchdog实际上就是一个线程，它运行在system_server进程中
2. Watchdog直接监测的是线程的looper状态，而这其中有一个looper在FgThread线程里，代表它的HandlerChecker是mMonitorChecker，它又监测了系统中重要的系统服务的状态
3. Watchdog里会不停的试探looper的queue和monitor的状态，如果超过1分钟无响应，就认为发生了死锁，并往trace文件里打印system_server进程的栈信息
4. 发生死锁后，Watchdog会根据是否有调试器连接以及是否设置"am hang"来决定要不要杀死system_server

