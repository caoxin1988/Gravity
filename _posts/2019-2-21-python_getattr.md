---
layout: post
title:  "python的__getattr__和__getattribute__"
subtitle: dacaoxin
author: dacaoxin
date:   2018-2-20 19:43:00
catalog:  true
tags:
    - python
---

## 1. 调用顺序

python中类有两个魔法函数，__getattribute__()和__getattr__(), 这两个都是python类对象访问属性时会被调用的， 当有下面的代码：

```
class A:
    def __init__(self):
        self.name = 'ttt'

a = A()
print(a.name)
print(a.ttt)    # 这时会报错
```

* 只要是使用类对象访问对象，第一步都会调用__getattribute__()这个魔法函数。
* 如果访问的类对象不存在，比如上面的a.ttt, 这个时候就会尝试调用__getattr__(), 如果没有实现, 就会抛出异常。 

## 2. __getattr__()的用处

上面说过__getattr__()是在类属性不存在的时候会被调用，因此这个方法就可以用来作一些巧妙的使用。

```
class Student:
    def __init__(self, **args):
        self.info = args

    def __getattr__(self, name):
        return self.info[name]

stu = Student(name= 'jack', age = 18)
print(stu.name)
```
