---
layout: post
title:  "python编程技巧总结"
subtitle: dacaoxin
author: dacaoxin
date:   2018-12-6 23:23:00
catalog:  true
tags:
    - python
---

## 1. python编程技巧总结

* 交换操作

如果想要交换x, y的值，python中可以直接这样写：

```
    x, y = y, x
```

* 善用enumerate()遍历list

写代码时不可避免的要同时用到列表的元素下标和元素值，大多数人的写法是：

```
a = ['a', 'b', 'c']
for i in range(len(a)):
    print(i, a[i])
```

而更好的写法是使用内置的enumerate()：

```
a = ['a', 'b', 'c']
for i, val in enumerate(a):
    print(i, val)
```

* python中使用dict来替代switch..case

* 使用if/else
> tmp = x if x > 5 else 0

* 使用list, set, dict推导式，比如列表推导式的性能比一般的列表操作性能要高，但是最好不要使用列表推导式实现复杂逻辑，会将低代码可读性

1. list

> l = ['abc' for _ in range(10)]

> l1 = [i for i in range(10) if i % 3]

> l1 = [i if i % 3 else 0 for i in range(10)]

2. set

> s = {i for i in range(5)}

3. dict

mydict = {'a' : 1, 'b' : 2}
> d = {k : v+2 for k, v in mydict.items()}

* dict作为函数参数时使用技巧

```
    def func(**dictargs):
        # 利用字典的pop方法取出传进来的参数
        name = dictargs.pop('name', 'default_name')
        age = dictargs.pop('age', 10)
```