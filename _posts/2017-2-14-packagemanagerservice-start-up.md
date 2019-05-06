---
layout: post
title:  "PackageManagerService启动过程"
subtitle: dacaoxin
author: dacaoxin
date:   2017-2-14 15:16:00
catalog:  true
tags:
    - android
    - framework
    - pkms
---

很长时间以来，我就想弄清楚Android的PackageManagerService具体做了什么工作，以及以后如何能够在开机阶段对系统速度进行优化。这次终于有机会来做这件事，这里会从多个方面来分析这个服务。这里先看看PMS的启动流程:

# 1. PackageManagerService类关系

从全局来看，PackageManagerService的类继承关系:

![PackageManagerService](/images/pkms/pkms.jpg)

# 2. PackageManagerService启动流程  

PackageManagerService是一个系统的关键service, 它是通过systemserver进程启动的，同时会将自己注册到servicemanager当中，其它进程需要使用的时候，
需要通过Binder获取packagemanagerservice的服务代理，通过RPC调用使用这个服务。

[-> frameworks/base/services/java/com/android/server/SystemServer.java]

    private void startBootstrapServices() {
        ... ... 
        // Start the package manager.
        Slog.i(TAG, "Package Manager");
        // 调用PackageManagerService.java的main()方法，将自己注册到systemserver进程中
        mPackageManagerService = PackageManagerService.main(mSystemContext, installer,
                mFactoryTestMode != FactoryTest.FACTORY_TEST_OFF, mOnlyCore);
        
        // 
        mFirstBoot = mPackageManagerService.isFirstBoot();
        mPackageManager = mSystemContext.getPackageManager();
        ... ...
    }


    private void startOtherServices() {
        ... ... 
        // 执行dexopt
        mPackageManagerService.performBootDexOpt();
        
        // 调用很多hasSystemFeature()这样的方法
        mPackageManager.hasSystemFeature(PackageManager.FEATURE_MIDI)
        // 调用PackageManagerService.java的systemReady()方法
        mPackageManagerService.systemReady();
    }
    
可以看到，SystemServer在启动PackageManagerService时，流程依次是：
* 调用PackageManagerService.java的main()方法, 见4.1
* 执行PackageManagerService.java的performBootDexOpt()方法， 见4.2
* 执行PackageManagerService.java的systemReady()方法，见4.3

# 3. PackageManagerService的构造方法  

这里先来分析一下PMS的构造函数，这个函数很长, 需要一节一节的分析

## 3.1 PMS前期准备

[-> frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java]

    public PackageManagerService(Context context, Installer installer,
            boolean factoryTest, boolean onlyCore)
    {
        // 存储APK的显示信息相关
        mMetrics = new DisplayMetrics();
        
        // Settings类, 具体工作内容见3.1.1
        mSettings = new Settings(context);
        mSettings.addSharedUserLPw("android.uid.system", Process.SYSTEM_UID,
                ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_PRIVILEGED);
        mSettings.addSharedUserLPw("android.uid.phone", RADIO_UID,
                ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_PRIVILEGED);
        mSettings.addSharedUserLPw("android.uid.log", LOG_UID,
                ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_PRIVILEGED);
        mSettings.addSharedUserLPw("android.uid.nfc", NFC_UID,
                ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_PRIVILEGED);
        mSettings.addSharedUserLPw("android.uid.bluetooth", BLUETOOTH_UID,
                ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_PRIVILEGED);
        mSettings.addSharedUserLPw("android.uid.shell", SHELL_UID,
                ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_PRIVILEGED);
        
        // 记录Installer类和PackageDexOptimizer类对象
        mInstaller = installer;
        mPackageDexOptimizer = new PackageDexOptimizer(this);
        
        // SystemConfig类，扫描系统权限，具体工作内容见3.1.2
        SystemConfig systemConfig = SystemConfig.getInstance();
        mGlobalGids = systemConfig.getGlobalGids();
        mSystemPermissions = systemConfig.getSystemPermissions();
        mAvailableFeatures = systemConfig.getAvailableFeatures();
        
        // 后面的3.2再分析
        ... ...
    }
    
### 3.1.1 Settings类addSharedUserLPw操作

先看看Settings类的构造函数

[-> frameworks/base/services/core/java/com/android/server/pm/Settings.java]

    Settings(File dataDir, Object lock) {
        mLock = lock;
        
        mRuntimePermissionsPersistence = new RuntimePermissionPersistence(mLock);
        
        mSystemDir = new File(dataDir, "system");
        mSystemDir.mkdirs();
        FileUtils.setPermissions(mSystemDir.toString(),
                FileUtils.S_IRWXU|FileUtils.S_IRWXG
                |FileUtils.S_IROTH|FileUtils.S_IXOTH,
                -1, -1);
        mSettingsFilename = new File(mSystemDir, "packages.xml");
        mBackupSettingsFilename = new File(mSystemDir, "packages-backup.xml");
        mPackageListFilename = new File(mSystemDir, "packages.list");
        FileUtils.setPermissions(mPackageListFilename, 0640, SYSTEM_UID, PACKAGE_INFO_GID);
        
        // Deprecated: Needed for migration
        mStoppedPackagesFilename = new File(mSystemDir, "packages-stopped.xml");
        mBackupStoppedPackagesFilename = new File(mSystemDir, "packages-stopped-backup.xml");
    }
    
其实就是构造了几个文件变量：

|mSystemDir                 |/data/system/                      |
|---------------------------|-----------------------------------|
|mSettingsFilename          |/data/system/packages.xml          |
|mBackupSettingsFilename    |/data/system/packages-backup.xml   |
|mPackageListFilename       |/data/system/packages.list         |
|mStoppedPackagesFilename   |/data/system/packages-stopped.xml  |
|mBackupStoppedPackagesFilename|/data/system/packages-stopped-backup.xml    |

/data/system/packages.xml里记录了每个apk的所有属性和权限信息，它是由PMS生成的，当系统中的APK有任何改变的时候，PMS都会修改这个文件  
/data/system/packages.list记录了每个apk的包名，UID， data路径以及GID    
Settings.java里有很多数据结构，这些数据结构对PMS非常重要，会在《PackageManagerService之数据结构》里专门分析  

接着来分析一下addSharedUserLPw()方法所做的工作:    

[-> frameworks/base/services/core/java/com/android/server/pm/Settings.java]


    SharedUserSetting addSharedUserLPw(String name, int uid, int pkgFlags, int pkgPrivateFlags) {
        SharedUserSetting s = mSharedUsers.get(name);
        if (s != null) {
            // mSharedUsers里对每一个uid只保存一份
            if (s.userId == uid) {
                return s;
            }
            PackageManagerService.reportSettingsProblem(Log.ERROR,
                    "Adding duplicate shared user, keeping first: " + name);
            return null;
        }
        // 没有这个uid，就新建一个SharedUserSetting
        s = new SharedUserSetting(name, pkgFlags, pkgPrivateFlags);
        s.userId = uid;
        // 把每个SharedUserSetting对象保存到对应的uid数组里
        // mUserIds和mOtherUserIds分别保存非系统应用ID和系统应用ID号对应的对象
        if (addUserIdLPw(uid, s, name)) {
            // 把这个新建的SharedUserSetting放到mSharedUsers里
            mSharedUsers.put(name, s);
            return s;
        }
        return null;
    }
    
关于SharedUserSetting.java中的数据结构详细列表，可以在《PackageManagerService之数据结构》里找到, 再看看addUserIdLPw()方法

[-> frameworks/base/services/core/java/com/android/server/pm/Settings.java]

    private boolean addUserIdLPw(int uid, Object obj, Object name) {
        if (uid > Process.LAST_APPLICATION_UID) {
            return false;
        }
        // 非系统应用的UID会大于10000
        if (uid >= Process.FIRST_APPLICATION_UID) {
            int N = mUserIds.size();
            final int index = uid - Process.FIRST_APPLICATION_UID;
            while (index >= N) {
                mUserIds.add(null);
                N++;
            }
            if (mUserIds.get(index) != null) {
                PackageManagerService.reportSettingsProblem(Log.ERROR,
                        "Adding duplicate user id: " + uid
                        + " name=" + name);
                return false;
            }
            mUserIds.set(index, obj);
        } else {        // 系统应用的UID小于10000
            if (mOtherUserIds.get(uid) != null) {
                PackageManagerService.reportSettingsProblem(Log.ERROR,
                        "Adding duplicate shared id: " + uid
                                + " name=" + name);
                return false;
            }
            mOtherUserIds.put(uid, obj);
        }
        return true;
    }
    
其实就是创建了Settings的类对象mSettings，然后让它的成员mSharedUsers里以类似于“android.uid.system”为索引对应的SharedUserSetting对象; 并同时将SharedUserSetting对象存到
mUserIds和mOtherUserIds中; 同时初始化了几个文件对象，这些文件以后的内容会是系统中所有apk的信息。

### 3.1.2 SystemConfig类扫描权限

SystemConfig是个单例，先看看构造函数：

[-> frameworks/base/services/core/java/com/android/server/SystemConfig.java]

    SystemConfig() {
        // Read configuration from system
        readPermissions(Environment.buildPath(
                Environment.getRootDirectory(), "etc", "sysconfig"), false);
        // Read configuration from the old permissions dir
        readPermissions(Environment.buildPath(
                Environment.getRootDirectory(), "etc", "permissions"), false);
        // Only read features from OEM config
        readPermissions(Environment.buildPath(
                Environment.getOemDirectory(), "etc", "sysconfig"), true);
        readPermissions(Environment.buildPath(
                Environment.getOemDirectory(), "etc", "permissions"), true);
    }
    
Environment.getRootDirectory()和Environment.getOemDirectory()分别是"/system"和"/oem"

[-> frameworks/base/services/core/java/com/android/server/SystemConfig.java]

    void readPermissions(File libraryDir, boolean onlyFeatures) {
        File platformFile = null;
        for (File f : libraryDir.listFiles()) {
            // We'll read platform.xml last
            if (f.getPath().endsWith("etc/permissions/platform.xml")) {
                platformFile = f;
                continue;
            }
            // 过滤掉非xml文件
            if (!f.getPath().endsWith(".xml")) {
                Slog.i(TAG, "Non-xml file " + f + " in " + libraryDir + " directory, ignoring");
                continue;
            }
            // 真正解析xml文件的
            readPermissionsFromXml(f, onlyFeatures);
        }
        
        // 最后才解析etc/permissions/platform.xml, 所以这个文件里的配置很重要
        if (platformFile != null) {
            readPermissionsFromXml(platformFile, onlyFeatures);
        }
    }
    
[-> frameworks/base/services/core/java/com/android/server/SystemConfig.java]

    private void readPermissionsFromXml(File permFile, boolean onlyFeatures) {
        FileReader permReader = null;
        
        permReader = new FileReader(permFile);
         while (true) {
                XmlUtils.nextElement(parser);
                if (parser.getEventType() == XmlPullParser.END_DOCUMENT) {
                    break;
                }
                
                String name = parser.getName();
                // HTML头为group的项
                if ("group".equals(name) && !onlyFeatures) {
                    String gidStr = parser.getAttributeValue(null, "gid");
                    if (gidStr != null) {
                        int gid = android.os.Process.getGidForName(gidStr);
                        mGlobalGids = appendInt(mGlobalGids, gid);
                    } else {
                        Slog.w(TAG, "<group> without gid in " + permFile + " at "
                                + parser.getPositionDescription());
                    }
                    XmlUtils.skipCurrentTag(parser);
                    continue;
                // HTML头为permission的项
                } else if ("permission".equals(name) && !onlyFeatures) {
                    String perm = parser.getAttributeValue(null, "name");
                    if (perm == null) {
                        Slog.w(TAG, "<permission> without name in " + permFile + " at "
                                + parser.getPositionDescription());
                        XmlUtils.skipCurrentTag(parser);
                        continue;
                    }
                    perm = perm.intern();
                    readPermission(parser, perm);
                } else ... ...
    }
    
读取这些etc/permissions/下的各种.xml文件之后，解析的结果如下：     
1. 对于"group"开头的项，在systemConfig对象的mGlobalGids里存入描述的gid
2. 对于"permission"开头的项，在systemConfig对象的ArrayMap<String, PermissionEntry> mPermissions里以name为key,存入一个PermissionEntry对象
3. 对于"assign-permission"开头的项，在systemConfig对象的SparseArray<ArraySet<String>> mSystemPermissions里以uid为key,存入各种权限名字的集合
4. 对于"library"开头的项，在systemConfig对象的ArrayMap<String, String> mSharedLibraries里以name为key,存入对应的文件名
5. 对于"feature"开头的项，在systemConfig对象的ArrayMap<String, FeatureInfo> mAvailableFeatures里以name为吸，存入FeatureInfo对象

## 3.2 PMS扫描工作

[-> frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java]

    public PackageManagerService(Context context, Installer installer,
            boolean factoryTest, boolean onlyCore) {
        ... ... 
        
        // 构造一些文件句柄, 后面扫描使用
        File dataDir = Environment.getDataDirectory();
        mAppDataDir = new File(dataDir, "data");
        mAppInstallDir = new File(dataDir, "app");
        mAppLib32InstallDir = new File(dataDir, "app-lib");
        mAsecInternalPath = new File(dataDir, "app-asec").getPath();
        mUserAppDataDir = new File(dataDir, "user");
        mDrmAppPrivateInstallDir = new File(dataDir, "app-private");
        
        // 把systemConfig对象的mPermissions变量的值转给mSettings的mPermissions对象
        ArrayMap<String, SystemConfig.PermissionEntry> permConfig
                    = systemConfig.getPermissions();
        for (int i=0; i<permConfig.size(); i++) {
            SystemConfig.PermissionEntry perm = permConfig.valueAt(i);
            BasePermission bp = mSettings.mPermissions.get(perm.name);
            if (bp == null) {
                bp = new BasePermission(perm.name, "android", BasePermission.TYPE_BUILTIN);
                mSettings.mPermissions.put(perm.name, bp);
            }
            if (perm.gids != null) {
                bp.setGids(perm.gids, perm.perUser);
            }
        }
        
        // 把systemConfig对象的mSharedLibraries变量的值复制给PMS的mSharedLibraries变量
        ArrayMap<String, String> libConfig = systemConfig.getSharedLibraries();
        for (int i=0; i<libConfig.size(); i++) {
            mSharedLibraries.put(libConfig.keyAt(i),
                    new SharedLibraryEntry(libConfig.valueAt(i), null));
        }
        
        // 从/data/system/packages.xml中读取系统已保存的app的信息, 这个文件在第一次开机的时候是不存在的
        // 以后再分析
        mRestoredSettings = mSettings.readLPw(this, sUserManager.getUsers(false),
                    mSdkVersion, mOnlyCore);
                    
        // 定义一个集合，里面保存明确不需要在这里进行dexopt操作的jar包和apk
        final ArraySet<String> alreadyDexOpted = new ArraySet<String>();
        
        // 通过adb shell env可以看到这两个环境变量的值，由于zygote启动时已经dexopt过这里的jar包，所以这里直接跳过
        final String bootClassPath = System.getenv("BOOTCLASSPATH");
            final String systemServerClassPath = System.getenv("SYSTEMSERVERCLASSPATH");
            
        if (bootClassPath != null) {
            String[] bootClassPathElements = splitString(bootClassPath, ':');
            for (String element : bootClassPathElements) {
                alreadyDexOpted.add(element);
            }
        } else {
            Slog.w(TAG, "No BOOTCLASSPATH found!");
        }
        
        if (systemServerClassPath != null) {
            String[] systemServerClassPathElements = splitString(systemServerClassPath, ':');
            for (String element : systemServerClassPathElements) {
                alreadyDexOpted.add(element);
            }
        } else {
            Slog.w(TAG, "No SYSTEMSERVERCLASSPATH found!");
        }
        // 确认mSharedLibraries里的jar包是否需要dexopt, 如果需要，在这里进行
        for (SharedLibraryEntry libEntry : mSharedLibraries.values()) {
            final String lib = libEntry.path;
            if (lib == null) {
                continue;
            }
            
            int dexoptNeeded = DexFile.getDexOptNeeded(lib, null, dexCodeInstructionSet, false);
            if (dexoptNeeded != DexFile.NO_DEXOPT_NEEDED) {
                // dexopt操作实际上都是通过installd执行的
                alreadyDexOpted.add(lib);
                mInstaller.dexopt(lib, Process.SYSTEM_UID, true, dexCodeInstructionSet, dexoptNeeded);
            }
        }
        // 扫描/system/framework/目录下的文件
        File frameworkDir = new File(Environment.getRootDirectory(), "framework");
        // 下面两个文件里已经知道是没有代码的，所以不需要dexopt
        alreadyDexOpted.add(frameworkDir.getPath() + "/framework-res.apk");
        alreadyDexOpted.add(frameworkDir.getPath() + "/core-libart.jar");
        String[] frameworkFiles = frameworkDir.list();
        if (frameworkFiles != null) {
            for (String dexCodeInstructionSet : dexCodeInstructionSets) {
                for (int i=0; i<frameworkFiles.length; i++) {
                    File libPath = new File(frameworkDir, frameworkFiles[i]);
                    String path = libPath.getPath();
                    // 跳过这个目下已经dexopt过的文件
                    if (alreadyDexOpted.contains(path)) {
                        continue;
                    }
                    // dexopt只针对这个目录下的apk和jar文件
                    if (!path.endsWith(".apk") && !path.endsWith(".jar")) {
                        continue;
                    }
                    // 确认是否需要执行dexopt操作
                    int dexoptNeeded = DexFile.getDexOptNeeded(path, null, dexCodeInstructionSet, false);
                    if (dexoptNeeded != DexFile.NO_DEXOPT_NEEDED) {
                        mInstaller.dexopt(path, Process.SYSTEM_UID, true, dexCodeInstructionSet, dexoptNeeded);
                    }
                }
            }
        }
        
        // 扫描/system/priv-app下的apk文件, 关于scanDirLI，在3.2.1里详细分析
        final File privilegedAppDir = new File(Environment.getRootDirectory(), "priv-app");
        scanDirLI(privilegedAppDir, PackageParser.PARSE_IS_SYSTEM
                | PackageParser.PARSE_IS_SYSTEM_DIR
                | PackageParser.PARSE_IS_PRIVILEGED, scanFlags, 0);
                
        // 扫描/system/app下的apk文件
        final File systemAppDir = new File(Environment.getRootDirectory(), "app");
        scanDirLI(systemAppDir, PackageParser.PARSE_IS_SYSTEM
                | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);
                
        ... ...
    }

这段代码虽然很长，但是功能却很单一：    
1. 扫描/system/framework/目录下的jar包和apk文件，对这些jar包进行dexopt优化     
2. 解析几个目录下的apk文件，然后把每个apk里的组件信息全部取出来，放到对应的数据结构中，以便后面使用。    

## 3.3 PMS扫尾工作

    public PackageManagerService(Context context, Installer installer,
            boolean factoryTest, boolean onlyCore) {
        ... ... 
        
        //删除零生文件
        deleteTempPackageFiles();
        
        if (!mOnlyCore) {
            // 处理一些第三方app
                    SystemClock.uptimeMillis());
            scanDirLI(mAppInstallDir, 0, scanFlags | SCAN_REQUIRE_KNOWN, 0);
            
            scanDirLI(mDrmAppPrivateInstallDir, PackageParser.PARSE_FORWARD_LOCK,
                    scanFlags | SCAN_REQUIRE_KNOWN, 0);
        }
        
        // 更新正确的library路径
        updateAllSharedLibrariesLPw();
        // 更新packages的权限信息
        updatePermissionsLPw(null, null, updateFlags);
        
        // 进行内存回收
        Runtime.getRuntime().gc();
    }


# 4. 继续分析SystemServer中操作PMS

## 4.1 PackageManagerService的main()方法：

[-> frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java]

    public static PackageManagerService main(Context context, Installer installer,
            boolean factoryTest, boolean onlyCore) {
        // new一个PackageManagerService对象, 见第3章分析构造函数
        PackageManagerService m = new PackageManagerService(context, installer,
                factoryTest, onlyCore);
        // 把PackageManagerService添加到servicemanager中
        ServiceManager.addService("package", m);
        return m;
    }

其实就是构造一个PackageManagerService对象，然后将它加入到servicemanager进程中进行管理。

## 4.2 PkMS的performBootDexOpt()方法

在SystemServer的startOtherServices()方法里调用performBootDexOpt()执行dexopt操作, 这里才是真正做事的地方。

[-> frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java]

    public void performBootDexOpt() {
        enforceSystemOrRoot("Only the system can request dexopt be performed");
        
        IMountService ms = PackageHelper.getMountService();
        if (doTrim) {
            if (!isFirstBoot()) {
                try {
                    // 显示提示文件
                    ActivityManagerNative.getDefault().showBootMessage(
                            mContext.getResources().getString(
                                    R.string.android_upgrading_fstrim), true);
                } catch (RemoteException e) {
                }
            }
            // 有需要的话，执行fstrim操作, 应该是类似于优化磁盘的操作
            ms.runMaintenance();
        }
        
        ... ... 
        
        final ArraySet<PackageParser.Package> pkgs;
        synchronized (mPackages) {
            pkgs = mPackageDexOptimizer.clearDeferredDexOptPackages();
        }
        
        if (pkgs != null) {
        ... ...
        
            ArrayList<PackageParser.Package> sortedPkgs = new ArrayList<PackageParser.Package>();
            // 添加core app到sortedPkgs里
            for (Iterator<PackageParser.Package> it = pkgs.iterator(); it.hasNext();) {
                PackageParser.Package pkg = it.next();
                if (pkg.coreApp) {
                    if (DEBUG_DEXOPT) {
                        Log.i(TAG, "Adding core app " + sortedPkgs.size() + ": " + pkg.packageName);
                    }
                    sortedPkgs.add(pkg);
                    it.remove();
                }
            }
            
            ... ...
            // 下面还有一些APP要添加
            // 1. 监听ACTION_PRE_BOOT_COMPLETED的APP
            // 2. 系统APP
            // 3. 有过更新的系统APP
            // 4. 监听ACTION_BOOT_COMPLETED的APP
            // 5. 根据条件，过滤掉一些APP
            
            // 执行dexopt操作
            for (PackageParser.Package pkg : sortedPkgs) {
                long usableSpace = dataDir.getUsableSpace();
                if (usableSpace < lowThreshold) {
                    Log.w(TAG, "Not running dexopt on remaining apps due to low memory: " + usableSpace);
                    break;
                }
                // 这里调用PackageDexOptimizer.java的performDexOpt()，最终是调用installd执行dexopt操作
                // 关于installd，后面再来分析
                performBootDexOpt(pkg, ++i, total);
            }
        }
    }

## 4.3 PKMS的systemReady() 

在systemserver.java里，执行的PMS的最后一个函数，就是systemReady()。

    public void systemReady() {
        mSystemReady = true;
        
        ... ...
        
        // 执行PackageDexOptimizer.java和PackageInstallerService.java的systemReady()方法
        mInstallerService.systemReady();
        mPackageDexOptimizer.systemReady();
        
        ... ...
    }
