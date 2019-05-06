---
layout: post
title:  "kotlin学习object"
subtitle: dacaoxin
author: dacaoxin
date:   2017-7-16 13:06:00
catalog:  true
tags:
    - kotlin
    - android
---

记录一下Kotlin中object关键字的使用。

## 1. JAVA静态方法

在写JAVA代码的时候，经常会用到一些静态方法，特别是工具类里，在JAVA中静态方法定义如下：

    public class DataProviderManager {

        public static void registerDataProvider() {
            // ... ...
        }

        public static Collection<DataProvider> getAllDataProviders() {
            // ... ...
        }
    }

java中通过static关键字定义工具类里的方法，当要使用某个方法时，不需要创建对象，直接使用即可：

    Boolean ret = DataProviderManager.registerDataProvider();

## 2. Kotlin静态方法

静态方法在Kotlin中可以通过object关键字实现。

### 2.1 object class

如果一个类里全部是静态方法，那么在Kotlin中实现如下：

    object DataProviderManager {
        fun registerDataProvider(provider: DataProvider) {
            // ...
        }

        val allDataProviders: Collection<DataProvider>
            get() = // ...

    }

通过object关键字申明类，就可以申明静态方法, 使用的方法和java一样：

    DataProviderManager.registerDataProvider(...)

### 2.2 companion object

companion object的作用有点类似于JAVA中的静态内部类，它的使用方法如下：

    class MyClass {
        companion object Factory {
            fun create(): MyClass = MyClass()
        }
    }

create()方法可以直接按下面的方法调用:

    val instance = MyClass.create()


有一些类要做单例模式的时候，也是通过companion object来实现的。
