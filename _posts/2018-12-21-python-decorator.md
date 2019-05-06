---
layout: post
title:  "python的装饰器"
subtitle: dacaoxin
author: dacaoxin
date:   2018-12-21 8:00:00
catalog:  true
tags:
    - python
---

## 1. 函数装饰器

先看一下下面这段代码，它可以帮助我们更好的理解装饰器：

```
    import time

    def decorator(func):
        def wrapper():
            print('time = ', time.time())
            func()

        return wrapper

    def f1():
        print('this is a function f1')

    f = decorator(f1)
    f()
```

和闭包有很大的相似性, python中一切皆对象，因为f1函数也可以作为对象当作参数传递给函数, 上面这段代码变换一下：

```
    import time

    def decorator(func):
        def wrapper():
            print('time = ', time.time())
            func()

        return wrapper

    @decorator
    def f1():
        print('this is a function f1')

    f1()
```

这个就是一个函数装饰器, 使用@语法糖。它可以达到不需要改变原来函数调用方式，而给函数增加功能的目的。如果f1有参数，怎么办呢，看下面:

```
    import time

    def decorator(func):
        def wrapper(*args, **kw):
            print('time = ', time.time())
            print('args = ', args)
            func(*args, **kw)

        return wrapper

    @decorator
    def f1(a, b):
        print('this is a function f1', a, b)

    f1(10, 20)
```

```
    import time

    def decorator(func):
        def wrapper(*args):
            print('time = ', time.time())
            print('args = ', args)
            func(*args)

        return wrapper

    @decorator
    def f2(a, b, **kw):
        print('this is a function f1', a, b)
        print('this is a function f1', kw)

    f1(10, 20)
```

还有一点，一个函数可以同时增加多个装饰器。