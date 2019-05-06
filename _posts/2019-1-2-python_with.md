---
layout: post
title:  "python上下文管理器与with"
subtitle: dacaoxin
author: dacaoxin
date:   2019-1-1 19:00:00
catalog:  true
tags:
    - python
---

## 1. 几个基本概念

* 只有实现了上下文协议的对象才可以使用with语句
* 对于实现了上下文协议的对象，我们称为上下文管理器
* 一个对象，如果实现了__enter()__和__exit()__方法，那这个对象就实现在上下文协议
* 上下文表达式就是能返回一个上下文管理器的表达式

## 2. 示例

```
    class Resource:
    def __enter__(self):
        print('apply for resource')
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_tb:
            print('process exception')
        else:
            print('no exception')

        print('release resource')

        return True

    def get_resource(self):
        print('use this resource')

    with Resource() as resource:
        resource.get_resource()
```

下面几点说明是Python中上下文管理器的核心点：

1. with ... as ..语句里，as后的变量，是上下文管理器中__enter()__的返回值

2. __exit()__方法的作用除了回收资源之外，还需要用来处理一些异常。它需要额外的3个参数，分别表示的意义是：
    exc_type: 发生的异常类型
    exc_value: 发生的异常的具体原因
    exc_tb: 异常堆栈信息

    所以在with之下的代码发生异常或者正常运行完之后，都会进入__exit()__方法。区别在于，如果是异常的原因导致进入，以上三个值都是空

3. __exit()__方法是需要返回值的，如果不写，默认返回None, 相当于False:  
    如果返回True, 则异常直接在__exit()__里被截断，不会接着往外抛， 如果返回False, 则异常会接着往外抛