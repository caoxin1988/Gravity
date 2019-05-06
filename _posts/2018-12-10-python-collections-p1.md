---
layout: post
title:  "python之collections模块(一)"
subtitle: dacaoxin
author: dacaoxin
date:   2018-12-11 20:23:00
catalog:  true
tags:
    - python
---

## 1. 关于tuple

* tuple的引用可以重复赋值，如下所示是合法的

```
    name_tuple = ('zhangsan', 10)
    print(name_tuple)

    name_tuple = ('lisi', 20)
    print(name_tuple)
```

但是下面这样是不合法的：

```
    name_tuple = ('zhangsan', 10)
    name_tuple[0] = 'wangwu'
```

* tuple的拆包特性

tuple拆包有两种方式，如下所示：

```
    name_tuple = ('zhangsan', 10, 'wuhan')

    name, age, city = name_tuple
    print(name, age, city)

    name, *other = name_tuple
    print(name, other)
```

输出结果是：

```
zhangsan 10 wuhan
zhangsan [10, 'wuhan']
```

* tuple和list的区别

1. tuple和list都是有序数组，只不过tuple创建了就无法修改，list可以修改
2. 正是由于tuple不过变的特性，tuple的效率会比list高，所以如果只做查找，tuple是首选
3. tuple是只读的，所以是线程安全的
4. tuple是immutable的，所以可以hash, 因此可以作为dict的key, 而List则不可hash
5. tuple可拆包

## 2. namedtuple

* namedtuple初始化方式

namedtuple一般有四种初始化方式： 直接初始化， 通过tuple初始化，通过字典初始化, _make()方法

```
    from collections import namedtuple

    # define a namedtuple
    User = namedtuple('User', ['name', 'age', 'addr', 'edu'])
    name_tuple = ('zhangsan', 10, 'wuhan')

    user = User('zhangsan', 18, 'wuhan', 'master')
    user1 = User(*name_tuple, 'master')

    d = {
        'name1' : 'zhangsan',
        'age' : 18,
        'addr' : 'wuhan'
    }
    user = User(**d, edu = 'master')
```

下面是通过_make()方法构造namedtuple:

```
    from collections import namedtuple

    User = namedtuple('User', ['name', 'age', 'addr', 'edu'])

    l = ['zhangsan', 18, 'wuhan', 'master']
    user = User._make(l)

    d = {
        'name' : 'zhangsan',
        'age' : 20,
        'addr' : 'wuhan',
        'end' : 'master'
    }
    user1 = User._make(d)
```

* _asdict()方法转换成字典

```
    from collections import namedtuple

    User = namedtuple('User', ['name', 'age', 'addr', 'edu'])

    user = User('zhangsan', 18, 'wuhan', 'master')
    print(user._asdict())
```

输出结果是：

```
    OrderedDict([('name', 'zhangsan'), ('age', 18), ('addr', 'wuhan'), ('edu', 'master')])
```

可以看到_asdict()方法可以将namedtuple转化为有序字典

* 拆包

namedtuple的拆包特性和tuple一样

## 3. defaultdict

在使用python默认的dict的时候，经常会遇到这样一种场景，需要先判断dict中的Key是否存在，如果不存在，新建一个，如果存在，才能再追加数
据，如下：

```
    d = dict()
    for i in range(2):
        if 'a' not in d.keys():
            d['a'] = 1
        else:
            d['a'] = d['a'] + 1

    print(d)
```

默认的dict提供了一个方法叫setdefault(), 可以帮助我们省去很多工作：

```
    d = dict()
    d.setdefault('a', 0)
    for i in range(2):
        d['a'] = d['a'] + 1

    print(d)
```

这样是可以减少很多代码量，并且运行效率也会比前一种高，因为减少了一次查找操作。但是有个问题，如果dict中有很多key，或者我们预先并不知道
未来会有哪些key，这种做法也会显得没有那么简洁。这个时候，就需要defaultdict，defaultdict其实是dict的一个字类，对扩展了dict的一些
功能：

```
    name_dict = defaultdict(int)
    for i in range(2):
        name_dict['a'] = name_dict['a'] + 1
```

defaultdict构造函数的参数是一个可调用的对象，可以是int, list, set等，也可以是函数，lambda表达式。它的作用就是当一个key不存在的
时候，调用这个对象来为这个key生成一个默认值。

```
    name_dict = defaultdict(lambda : 1)
    for i in range(2):
        name_dict['a'] = name_dict['a'] + 1
```