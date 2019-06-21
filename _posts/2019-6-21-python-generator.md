---
layout: post
title:  "python3中迭代器和生成器"
author: dacaoxin
date:   2019-6-21 22:21:00
categories: [python]
---

> 更多精彩内容，欢迎关注微信公众号: tmac_lover

迭代器和生成器是python中一个很重要的语法，使用也很广泛。

## 迭代器
举个例子：

```python
for i in [1, 2, 3, 4]:
  print(i)
```

类似这样的代码平时很常见，这里其实就用到了迭代器。

### 可迭代对象
要理解迭代器，首先要理解可迭代对象。那什么是可迭代对像呢？

python内置的几种数据结构：字符串(str)，列表(list)，元组(tuple)，字典(dict)，集合(set)都是可迭代对象。

除此之外，那些实现了`__iter__()`魔法函数的对象，也是可迭代对象。比如：

```python
class MyIter:
  def __init__(self):
    pass

  def __iter__(self):
    yield 1	# __iter__()需要返回一个迭代器

a = MyIter()	# 对象a就是一个可迭代的对象
```

有两个很简单的判断是不是可迭代对象的方法：

```python
# -*- coding: utf-8 -*-
from collections.abc import Iterable

print(isinstance([1,2,3], Iterable))
```

或者：

```python
# -*- coding: utf-8 -*-
def is_iterable(obj):
  try:
    iter(obj)
      return True
  except Exception:
    return False
```

都可以判断对象是不是可迭代的(iterable)。

### 迭代器

迭代器可以通过`next()`方法不断重复获取下一个值，直到所有元素全部输出完之后，返回`StopIteration`才停止。在python3中同时实现在`__iter__()`和`__next__()`两个魔法函数的对象，就是迭代器。其中`__iter__()`方法需要返回一个**迭代器**, 而`__next__()`方法返回下一个返回值或者`StopIteration`。比如：

```python
class MyIter:
  def __init__(self):
    self.cnt = 0

  def __iter__(self):
    # 因为实现在__next__,所以自身就是一个迭代器,这里就可以返回自己
    return self

  def __next__(self):
    return 1
```

对可迭代的对象，使用`iter()`方法，也会返回一个迭代器，如：

```python
iter([1, 2, 3, 4])
```

文章开头的for循环遍历列表的例子，实际上在运行时，由解释器帮助我们对列表[1, 2, 3, 4]调用了`iter()`方法，将其转换成迭代器，然后每次使用`next()`取一个值出来。

## 生成器

生成器可以理解成一种特殊的迭代器。它和迭代器的区别在于，生成器并不是一上来就把所有值装载进内存，因而也不会占用大量的内存，只是在需要使用`next()`函数获取值的时候，才会取一个值返回，内存开销非常小。

python3中最简单的形式是生成器表达式，它有点像列表推导式：

```python
gen = (i for i in range(10000))
```

还有一种很常见的写法是在函数里使用`yield`返回一个生成器：

```python
def generator(k):
  i = 1
  while True:
    yield i ** k	#使用yield
    i += 1

gen = generator(2)
for i in range(4):
  sum = 0
  sum += next(gen)  #相当于每次使用next()之后，generator函数停止了
```
