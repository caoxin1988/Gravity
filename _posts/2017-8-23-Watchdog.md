---
layout: post
title:  "Watchdog重启实例分析"
subtitle: dacaoxin
author: dacaoxin
date:   2017-8-23 17:02
catalog:  true
tags:
    - rom
    - android
    - framework
---

## 1. 什么是Watchdog

对Android稍微有所了解的朋友应该都听过ANR这个东西，它的全称是ApplicationNotResponding, 也就是因为某种原因应用程序卡住了，没有任何响应。

其实在framework里，也会有类似ANR的东西产生，我们可以叫它是“SystemNotResponding”, 造成这个的原因是因为一些很重要的系统服务，比如AMS, PMS里发生了死锁。因为这些系统服务在Android
系统中非常重要，所以Android系统提供了一个很重要的机制来保证这些服务不会死锁，一旦有死锁发生，就让system_server进程重启，以保证秕可用。完成这项工作的就上Watchdog。

Watchdog字面上是“看门狗”的意思，有做过嵌入式低层的朋友应该知道，为了防止嵌入式系统MCU里的程序因为干扰而跑飞，专门在MCU里设计了一个定时器电路，叫做看门狗。当MCU正常工作的，每隔一段时间
会输出一个信号给看门狗，也就是所谓的喂狗。如果程序跑飞，MCU在规定的时间内没法喂狗，这时看门狗就会直接触发一个reset信号，让CPU重新启动。

在Android系统的framework中，设计了一个系统服务Watchdog，它类似于一个软件看门狗，用来保护重要的系统服务。它的源代码位于：

> frameworks/base/services/core/java/com/android/server/Watchdog.java

它运行于system_server进程中。

今天先用一个例子来演示一下Watchdog造成系统重启的问题如何分析，后面再从源代码的角度来解释Watchdog是如何完成这些工作的。

## 2. 确认Watchdog问题

如果你的Android系统突然卡住不动，不响应任何操作，然后从bootanimation阶段重启，并且在logcat中发现有下面的关键字，那一定是Watchdog起了作用。

    Watchdog: *** WATCHDOG KILLING SYSTEM PROCESS: Blocked in monitor xxx, Blocked in xxx
    Watchdog: xxx
    Watchdog: *** GOODBYE!

Watchgod会通过"kill -3"命令生成一份trace文件，位于/data/anr/trace.txt。trace文件很重要，通过它可以看到进程调用栈，方便我们确认死锁发生位置。

## 3. 实例分析

这是前段时间我在工作中碰到的一个问题。在我们的系统里安装了“沙发管家”这款APP之后，点击“沙发管家”里的【应用更新】时，整个系统卡住，接着系统从开机桢动画重启。拿到logcat之后，我发现下面这段：

    08-08 14:32:22.948  2257  2858 W Watchdog: *** WATCHDOG KILLING SYSTEM PROCESS: Blocked in monitor com.android.server.am.ActivityManagerService on foreground thread (android.fg), Blocked in handler on ui thread (android.ui)
    08-08 14:32:22.951  2257  2858 W Watchdog: foreground thread stack trace:
    08-08 14:32:22.951  2257  2858 W Watchdog:     at com.android.server.am.ActivityManagerService.monitor(ActivityManagerService.java:20307)
    08-08 14:32:22.951  2257  2858 W Watchdog:     at com.android.server.Watchdog$HandlerChecker.run(Watchdog.java:172)
    08-08 14:32:22.951  2257  2858 W Watchdog:     at android.os.Handler.handleCallback(Handler.java:739)
    08-08 14:32:22.951  2257  2858 W Watchdog:     at android.os.Handler.dispatchMessage(Handler.java:95)
    08-08 14:32:22.951  2257  2858 W Watchdog:     at android.os.Looper.loop(Looper.java:148)
    08-08 14:32:22.951  2257  2858 W Watchdog:     at android.os.HandlerThread.run(HandlerThread.java:61)
    08-08 14:32:22.951  2257  2858 W Watchdog:     at com.android.server.ServiceThread.run(ServiceThread.java:46)
    08-08 14:32:22.951  2257  2858 W Watchdog: *** GOODBYE!
    08-08 14:32:22.951  2257  2858 I Process : Sending signal. PID: 2257 SIG: 9

* 从log里看到在08-08 14:32:22.951时刻，Watchdog杀死了system_server进程。并且死锁是发生在android.ui这个线程。并且是ActivityManagerService这个系统服务里发生了死锁。

因为Android里所有的系统服务都运行在system_server进程，所以接下来在trace.txt里，查找14:32:22.951时刻左右的system_server进程的栈信息。我发现了下面的信息：

    "android.ui" prio=5 tid=12 Blocked
    ... ...
    at com.android.server.am.ActivityManagerService.dispatchUidsChanged(ActivityManagerService.java:3895)
    - waiting to lock <0x07d29b29> (a com.android.server.am.ActivityManagerService) held by thread 81
    ... ...

* android.ui线程被Blocked住，并且是被ActivityManagerService的<0x07d29b29>这个锁block。当前这个锁被system_server进程的81号线程所持有。并且我还发现，system_server中很多线程都block在81号线程。

接下来查找tid=81这个线程，找到如下栈信息：

    "Binder_F" prio=5 tid=81 Waiting
    ... ...
    at java.lang.Object.wait!(Native method)
    - waiting on <0x05f1c7e3> (a com.android.server.am.ContentProviderRecord)
    at com.android.server.am.ActivityManagerService.getContentProviderImpl(ActivityManagerService.java:10039)
    - locked <0x05f1c7e3> (a com.android.server.am.ContentProviderRecord)
    at com.android.server.am.ActivityManagerService.getContentProvider(ActivityManagerService.java:10063)
    at android.app.ActivityThread.acquireProvider(ActivityThread.java:4778)
    at android.app.ContextImpl$ApplicationContentResolver.acquireProvider(ContextImpl.java:2006)
    at android.content.ContentResolver.acquireProvider(ContentResolver.java:1421)
    at android.content.ContentResolver.acquireContentProviderClient(ContentResolver.java:1496)
    at com.funshion.android.ottsecurity.OttBlackWhites.allowShowWindow(OttBlackWhites.java:151)
    at com.android.server.am.ActivityStackSupervisor.isProtectApp(ActivityStackSupervisor.java:984)
    at com.android.server.am.ActivityStackSupervisor.checkIsSystemAppType(ActivityStackSupervisor.java:1035)
    at com.android.server.am.ActivityStackSupervisor.shouldStartActivityMayWait(ActivityStackSupervisor.java:1051)
    at com.android.server.am.ActivityStackSupervisor.startActivityLocked(ActivityStackSupervisor.java:1568)
    at com.android.server.am.ActivityStackSupervisor.startActivityMayWait(ActivityStackSupervisor.java:1193)
    - locked <0x07d29b29> (a com.android.server.am.ActivityManagerService)
    at com.android.server.am.ActivityManagerService.startActivityAsUser(ActivityManagerService.java:3995)
    at com.android.server.am.ActivityManagerService.startActivity(ActivityManagerService.java:3960)
    at android.app.ActivityManagerNative.onTransact(ActivityManagerNative.java:162)
    at com.android.server.am.ActivityManagerService.onTransact(ActivityManagerService.java:2553)
    at android.os.Binder.execTransact(Binder.java:453)

* 在ActivityStackSupervisor.java的startActivityMayWait()方法里持有<0x07d29b29>锁，并且线程一直在ActivityManagerService.java里的getContentProviderImpl()方法里wait锁<0x05f1c7e3>。并且因为锁
<0x05f1c7e3>一直没有被唤醒，造成<0x07d29b29>无法被释放，Watchdog在一段时间内一直无法拿到该锁，它就认为AMS有死锁产生，直接杀死system_server，造成系统重启。

* 从trace的栈信息中可以看到，startActivityMayWait()方法在ActivityStackSupervisor.java的第1193行开始持有锁<0x07d29b29>，从代码中看到1193行是

	synchronized(mService) {}

所以mService就是<0x07d29b29>，而mService其实就是ActivityManagerService对象。

到这里很明显，问题的焦点在于<0x05f1c7e3>这个锁为什么一直没有被唤醒？

再通过看getContentProviderImpl()方法的源码，会发现<0x05f1c7e3>这个锁是一个ContentProviderRecord对象。也就是说，在startActivity()时，需要使用某个ContentProvider，但是这个ContentProvider又无法被成功创建，
导致AMS对象锁<0x07d29b29>一直无法释放。

接着找源代码，从ActivityStackSupervisor.java的startActivityMayWait()方法开始找，果然发现在isProtectApp()方法里要用到一个provider,并且这个provider存在于一个普通的system app进程中。接着我用ps命令查看这个
app进程的状态，发现它并没有启动。这就让我很奇怪了，因为正常来讲，进程应该很容易启动起来。所以我又看了一遍启动app进程中provider的流程。启动一个新进程中的provider大致是这样的：

    main()  [ActivityThread.java]  -> attach() [ActivityThread.java]
    -> mgr.attachApplication(mAppThread) [ActivityThread.java]
    - binder -> attachApplication() [ActivityManagerService.java]
    -> thread.bindApplication() [ActivityManagerService.java]
    - binder -> handleBindApplication() [ActivityThread.java]
    -> installContentProviders() [ActivityThread.java]
    -> ActivityManagerNative.getDefault().publishContentProviders() [ActivityThread.java]
    - binder -> publishContentProviders() [ActivityManagerService.java]
    -> dst.notifyAll() [ActivityManagerService.java]

* dst也是一个ContentProviderRecord对象，它和ActivityManagerService.java的getContentProviderImpl()方法里的锁<0x05f1c7e3>是同一个对象。

到这里，一个正常新进程中的provider才被安装完成。在上面的流程中，我发现在ActivityManagerService.java的attachApplication()方法里，也要获取ActivityManagerService对象锁，也就是<0x07d29b29>这个锁。
但是从trace里tid=81线程中看到，这个锁一直被持有，并且无法释放，所以在这里，provider也无法被成功创建，这就是死锁的原因。

## 4. 解决办法与总结

通过上面一步一步的分析，原因就是：点击“沙发管家”的【应用更新】按键时，需要通过AMS启动一个新的activity； 启动activity方法在持有了AMS对象锁后又等待某个新的app进程里provider对象创建完成后，才释放AMS对象锁；
但是在启动一个新的app进程时，又需要持有AMS对象锁才能完成provider对象的安装，所以就陷入了死循环，导致AMS死锁。

知道了问题产生的原因，就比较好办了，我采用的方法是，将调用isProtectApp()方法的位置移到持有AMS对象锁之前，这样就解决了问题。

但是这样做并不好，我们最好不要让系统服务依赖普通的app进程，这样很容易造成上面这种类似的死锁。 我之所以这样改是因为这样最简单，否则的话，需要别的同事改很多代码。但是其实这并不是一件非常好的做法。

这篇文章用一个例子来告诉大家如何查找系统服务死锁的原因，后面还会有一篇文章来解释一下，Watchdog是如何来监测死锁的。
