---
layout: post
title:  "Kotlin学习之lambda"
subtitle: dacaoxin
author: dacaoxin
date:   2017-5-30 21:19:00
catalog:  true
tags:
    - kotlin
    - android
    - app
---

kotlin因为一个Google IO大会，一夜之间变成了最热门的编程语言和技术，接下来会有一系列的文章来介绍kotlin的一些基础知识以及其在android中的应用，
这里所写的基本上是学习[kotlin官网][http://kotlinlang.org/docs/reference/]时方便自己理解的总结。


先介绍一下高阶函数和lambda表达式。

## 1. 高阶函数

### 1.1 lock()

如果一个函数的某个参数类型或者返回值害型是函数，那么这个函数就是一个高阶函数。典型的高阶函数lock()如下：

	fun <T> lock(lock: Lock, body: () -> T): T {
		lock.lock()
		try {
			return body()
		}
		finally {
			lock.unlock()
		}
	}
	
lock()的第二个参数body就是一个函数类型，这个函数是一个没有参数，然后返回值是T的函数。

当我们使用lock()的时候，我们可以传入一个函数作为它的参数：

	fun toBeSynchronized() = sharedResource.operation()
	
	val result = lock(lock, ::toBeSynchronized)
	
更加方便的方式，就是传一个lambda表达式作为参数：

	val result = lock(lock, {sharedResource.operation()})

在kotlin中，如果一个函数的最后一个参数是一个函数类型，并且使用时传入的是一个lambda表达式，那么可以将它提到圆括号外面写：

	lock(lock) {
		sharedResource.operation()
	}

### 1.2 map()

再看一个例子map():

	fun <T, R> List<T>.map(transform: (T) -> R): List<R> {
		val result = arrayListOf<R>()
		for (item in this)
			result.add(transform(item))
		return result
	}

如果lambda表达式是函数的唯一参数，那圆括号可以省略：

	val doubled = ints.map { values -> values * 2 }

## 2. lambda表达式

一个完整的lambda表达式是像这样的:

	val sum = { x: Int, y: Int -> x + y }
	
或者

	val sum: (Int, Int) -> Int = { x, y -> x + y }
	
它最外层总是有大括号{}包围起来，如果返回值不是Unit, 表达式实体的最后一句话就作为返回值。

如果一个lambda表达式只有一个参数，那么可以省略掉这个参数，并且直接使用it代表它

## 3. lambda表达式的用处

在android中使用kotlin时，lambda表达式很重要的一个作用就是定义匿名函数，可以免去我们写只使用一次的函数；另一个很重要的作用就是可以简化java里的匿名内部类的写法。

### 3.1 匿名函数

匿名函数就是没有申明，但是直接以表达式的形式作为参数传递给其它函数的函数，如

	max(strings, { a, b -> a.length < b.length })

### 3.2 实现匿名内部类

在Android中非常典型的使用lambda表达式的例子就是实现View.setOnClickListener()方法。实现这样一个功能java的通常写法是：

	view.setOnClickListener(new OnClickListener(){
		@Override
		public void onClick(View v) {
			Toast.makeText(v.getContext(), "Click", Toast.LENGTH_SHORT).show();
		}
	})
	
将这段代码转化成kotlin代码：

	view.setOnClickListener(object : OnClickListener {
		override fun onClick(v: View) {
			toast("Click")
		}
	}
	
值得注意的是，kotlin允许对java作一些优化，如果interface中只有一个函数，那么interface可以直接被替换成这个函数，所以setOnClickListener方法
在kotlin中相当于被定义成：

	fun setOnClickListener( listener : (view) -> Unit )
	
根据上面所提到的一系列简化规则，这个实现最终变成：

	view.setOnClickListener({ view ->  toast("Click") })

	view.setOnClickListener() { view -> toast("Click") }
	
	view.setOnClickListener { view -> toast("Click") }

	view.setOnClickListener { toast("Click") }

## 4. 总结

关于kotlin对java代码的优化:

* 如果interface中只有一个函数，那么interface可以直接被替换成这个函数

关于lambda表达式的几点使用总结：

* 如果一个函数的最后一个参数是一个函数类型，并且使用时传入的是一个lambda表达式，那么可以将它提到圆括号外面写
* 如果lambda表达式是函数的唯一参数，那圆括号可以省略
* 如果一个lambda表达式只有一个参数，那么可以省略掉这个参数，并且直接使用it代表它
* 如果一个lambda表达式的参数并未使用，可以省略掉参数和->，或者将参数写为下划线_ (下划线是kotlin 1.1版本的新功能)
