---
layout: post
title:  "Android系统persist进程"
subtitle: dacaoxin
author: dacaoxin
date:   2017-7-25 8:23:00
catalog:  true
tags:
    - rom
    - android
    - persist
---

## 1. persist进程启动

在Android系统写app时，在AndroidManifest.xml里有这样一个属性：

	android:persistent="true" 
	
加上这个之后，则表明此应用是一个永久性应用，就是从系统一开机就一直运行，直到系统关机。

我们知道Android系统启动后，会有一个叫AMS(ActivityManagerService)的系统服务，在AMS的systemReady()方法里就会加载所有的
persist应用：

	public void systemReady(final Runnable goingCallback) {
        ... ...        
        try {
            List apps = AppGlobals.getPackageManager().
                getPersistentApplications(STOCK_PM_FLAGS);
            if (apps != null) {
                int N = apps.size();
                int i;                
                for (i=0; i<N; i++) {
                    ApplicationInfo info
                        = (ApplicationInfo)apps.get(i);   
                    if (info != null &&
                            !info.packageName.equals("android")) {
                        addAppLocked(info, false, null /* ABI override */);
                    }
                }
            }
        } catch (RemoteException ex) {            // pm is in same process, this will never happen.
        }

        ... ...
    }
	
代码中getPersistentApplications方法的实现在PKMS(PackageManagerService)中，

	public List<ApplicationInfo> getPersistentApplications(int flags)
    {
        ... ...        
        final Iterator<PackageParser.Package> i = mPackages.values().iterator();        
        while (i.hasNext()) {            
            final PackageParser.Package p = i.next();            
            if (p.applicationInfo != null
                    && (p.applicationInfo.flags&ApplicationInfo.FLAG_PERSISTENT) != 0
                    && (!mSafeMode || isSystemApp(p))) {
                ... ...
            }
        }
    }
	
这里找到系统中所有带persist属性的系统APP，传给AMS的addAppLocked()方法。

	final ProcessRecord addAppLocked(ApplicationInfo info, boolean isolated,
            String abiOverride) {
        ... ...

        app = newProcessRecordLocked(info, null, isolated, 0);        
        if ((info.flags & PERSISTENT_MASK) == PERSISTENT_MASK) {
            app.persistent = true;
            app.maxAdj = ProcessList.PERSISTENT_PROC_ADJ;
        }        
        if (app.thread == null && mPersistentStartingProcesses.indexOf(app) < 0) {
            mPersistentStartingProcesses.add(app);
            startProcessLocked(app, "added application", app.processName, abiOverride,                    
                     null /* entryPoint */, null /* entryPointArgs */);
        }
    }
	
addAppLocked()里设置这个进程persist属性，然后将这个进程加入到mPersistentStartingProcesses缓冲列表中，最后调用startProcessLocked()
启动进程。

当进程启动成功之后，便会从mPersistentStartingProcesses里删除这个进程。

## 2. persist进程重启机制

除了要一开机启动之外，persist的应用还需要能够保证其自身被杀死之后仍然可以重新启动起来，这样才能保证应用一直在运行。

我们知道每个应用进程启动时，都会调用ActivityThread的attach()方法将自己依附于AMS当中，也就是由AMS启动它并对它进行管理，attach()最终
通过binder机制调用到AMS的attachApplicationLocked()方法。

	private final boolean attachApplicationLocked(IApplicationThread thread,            int pid) {
        ... ...

        AppDeathRecipient adr = new AppDeathRecipient(
                    app, pid, thread);
        thread.asBinder().linkToDeath(adr, 0);
        app.deathRecipient = adr;

        ... ...
    }
	
每一个应用进程里都会有一个ApplicationThread mAppThread对象，AMS通过它在AMS里的代理接口IApplicationThread与应用进程
进行通信。上面这个方法的thread参数就是一个应用进程在AMS里的代理对象。

AppDeathRecipient类的申明：

	private final class AppDeathRecipient implements IBinder.DeathRecipient {        
		final ProcessRecord mApp;        
		final int mPid;        
		final IApplicationThread mAppThread;

        AppDeathRecipient(ProcessRecord app, int pid,
                IApplicationThread thread) {
            mApp = app;
            mPid = pid;
            mAppThread = thread;
        }        
        @Override
        public void binderDied() {            
            synchronized(ActivityManagerService.this) {
                appDiedLocked(mApp, mPid, mAppThread, true);
            }
        }
    }

当应用进程死掉时，系统会回调由linkToDeath()注册的AppDeathRecipient对象的binderDied()方法。具体调用关系如下：

	binderDied() -> appDiedLocked() -> handleAppDiedLocked()
    -> cleanUpApplicationRecordLocked()
	
最终调用到cleanUpApplicationRecordLocked()方法：

	private final boolean cleanUpApplicationRecordLocked(ProcessRecord app,            
                  boolean restarting, boolean allowRestart, int index) {
        ... ... 

        if (!app.persistent || app.isolated) {
            removeProcessNameLocked(app.processName, app.uid);            
            if (mHeavyWeightProcess == app) {    
                mHandler.sendMessage(mHandler.obtainMessage(CANCEL_HEAVY_NOTIFICATION_MSG,
                        mHeavyWeightProcess.userId, 0));
                mHeavyWeightProcess = null;
            }
        } else if (!app.removed) {            
            if (mPersistentStartingProcesses.indexOf(app) < 0) {
                mPersistentStartingProcesses.add(app);
                restart = true;
            }
        }

        ... ...
    }
	
可以看到，如果是非persist的进程死亡，则直接回收所有的进程资源，如果是persist的进程，就会再加入mPersistentStartingProcesses
队列，然后等待重启。

## 3. 总结

带persist属性的进程，从系统一起动，AMS完成之后就会被启动起来，然后直到系统关机。中间如果被OOM或者人为的杀掉，系统仍然后自动重启这些进程。这
也就是persist的含义。

当然这里面涉及到的有些知识比较复杂，在这里只是简要的说明了调用流程，具体感兴趣的可以阅读源码仔细分析。
