---
layout: post
title:  "python双端队列deque"
subtitle: dacaoxin
author: dacaoxin
date:   2018-2-13 12:23:00
catalog:  true
tags:
    - python
---

## 1. 什么是deque

在写代码的时候，经常会使用list列表这种数据结构，当然python内置的list也能满足我们绝大多数的操作要求。但是当我们需要更高性能的时候，
list的有些操作就不能满足我们要求，不过python的collections模块为我们提供了一个deque的数据结构。

deque是'double-ended queue'的缩写，它是一个线程安全的数据结构，它的操作和list非常相似，但是它是可以两端append和pop的。并且，append()
和pop()操作的时间复杂度都是O(1)。而list的pop(0)和insert(0, v)的时间复杂度是O(n)。

deque在初始化的时候，需要指定一个最大长度，如果没有指定或者长度为None的话，deque将会被分配一个任意的长度。如果指定了长度的话，当从
deque的一端插入元素时，若此时队列已满，则另一端的第一个元素会被自动弹出。

初始化deque的方法:

```
from collections import deque
deq = deque(maxlen = 5) # 最大长度是5的双端队列
deq1 = deque()
```

## 2. deque支持的方法

* deque和list一样，支持下标索引操作，但是deque不支持切片

```
from collections import deque

deq = deque(['a', 'b', 'c', 'd'])
print(deq)
print(deq[-1] # 返回 d
print(deq[0:2]) # 错误，不支持切片

```

* append()和appendleft()

deque支持和List一样的append()，从右端插入；同时添加了appendleft()方法，类似于list的append(0), 但是效率更高

```
from collections import deque

deq = deque()
deq.append(1)
deq.appendleft(2)
```

* pop()和popleft()

这两个方法和apend()以及appendleft()类似。

```
from collections import deque

deq = deque('a', 'b', 'c', 'd')
print(deq.pop())    # 打印出'd'
print(deq.popleft())     # 打印出'a'

```

* len()

和list一样，可以使用len()取得deque的长度

* rotate()

deque支持一个很有意思的方法叫rotate(n = 1), 当n是正数时，表示从左往右循环移n位，当n是负数时，表示从右往左循环移n位
比如deq.rotate(1)相当于deq.appendleft(deq.pop())

```
from collections import deque

deq = deque('a', 'b', 'c', 'd')``
print(deq)  # 打印deque(['a', 'b', 'c', 'd'])

deq.rotate(1)
print(deq)  # 打印deque(['d', 'a', 'b', 'c'])

deq.rotate(-1)
print(deq)  # 打印deque(['a', 'b', 'c', 'd'])
```
