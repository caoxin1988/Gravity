---
layout: post
title:  "Android Java Thread"
subtitle: dacaoxin
author: dacaoxin
date:   2017-2-16 10:11:00
catalog:  true
tags:
    - android
    - framework
    - thread
    - java
---

## 1. Thread.java类

先来看下Thread类的继承关系和构造函数：

    public class Thread implements Runnable {
        
        public Thread() {
            create(null, null, null, 0);
        }
        
        // 最常用的一个构造函数，通过重写Runnable类中的run()方法，实现Thread的主体
        public Thread(Runnable runnable) {
            create(null, runnable, null, 0);
        }
        
        public Thread(Runnable runnable, String threadName) {
            if (threadName == null) {
                throw new NullPointerException("threadName == null");
            }
            
            create(null, runnable, threadName, 0);
        }
        
        // 可以看到，start()之后线程才真正的创建出来
        public synchronized void start() {
            checkNotStarted();
         
            hasBeenStarted = true;
         
            nativeCreate(this, stackSize, daemon);
        }
     
        private native static void nativeCreate(Thread t, long stackSize, boolean daemon);
        
    }

## 2. 如何创建线程

### 2.1 继承Thread

    public class ThreadTest extends Thread {
        // 重写run方法
        public void run() {
                System.out.println("I'm running!");
        }
    }
    
    ThreadTest tt = new ThreadTest();
    tt.start();
    
### 2.1 实现Runable

    Thread t = new Thread(new Runable() {
        public void run() {
            System.out.println("I'm running!");
    }
    });
    
    t.start();

## 3. sleep()和wait()的区别

* sleep()方法是Thead.java类的一个静态方法，而wait()是object类的方法
* wait()方法会释放当前线程所持有的对象锁，而sleep()不会释放
* wait()是能过notify()唤醒，而sleep()是通过时间超时之后唤醒
* waite()和notify()必须在synchronized函数或synchronized　block中进行调用。如果在non-synchronized函数或non-synchronized　block中进行调用，虽然能编译通过，但在运行时会发生IllegalMonitorStateException的异常
