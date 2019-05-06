---
layout: post
title:  "python3中tuple比较"
subtitle: dacaoxin
author: dacaoxin
date:   2019-2-6 16:46:00
catalog:  true
tags:
    - python
---

今天在使用python的PriorityQueue时遇到一个关于tuple比较问题，搞了半天才找到真实原因，记录一下。先看例子：

```
    class Node:
        def __init__(self, x):
            self.val = x

    a = (1, Node(10))
    b = (1, Node(20))
    print(a > b)
```

这段代码在python3下运行是会报错的，错误是TypeError: '>' not supported between instances of 'Node' and 'Node', 但是当我把这段
代码改成Python2的版本，却不会报错。

我们知道无论是python2中关于tuple的比较，都是从tuple的第0个元素开始，依次往后比，即第0个比不出来，就比第1个，再比第2个，
依次类推...，那为什么同样的代码，在python2中可以通过，但是python3中却会抛出异常呢？难道是因为Python3中更改了对tuple的比较操作吗。

后来google一圈之后，我找到[python3 ordering-comparisons](https://docs.python.org/3/whatsnew/3.0.html#ordering-comparisons),
这里有三点需要注意：

* 在python3中，如果比较操作符两端是没有意义的对象进行比较，就会抛出TypeError的异常
* 对于内置的sorted()方法和List的sort()方法，不再支持key参数，即不再允许自定义比较函数作为参数
* cmp()函数和__cmp__()这个魔法函数都不再存在，所以如果想对类对象进行比较，需要通过__lt__(), __eq__(), __hash__()之类的魔法函数实现

回到我的问题，因为a[0] == b[0], 所以需要比较Node(10)和Node(20)这两个对象的大小，但class Node并没有实现__lt__()或者__ge__()之类的可
用于比较的魔法函数，所以这里会抛出TypeError异常，告知我们无法使用>符号。

其实我今天所遇到的问题是因为使用了python3中的PriorityQueue, 因为PriorityQueue是使用堆来实现，而往堆里插入新值的时候，是需要对元素进行比较的，
而我插入的正是一个元组，所以实际上正是两个元组进行比较。

