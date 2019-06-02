---
layout: post
title:  "python基础之函数"
author: dacaoxin
date:   2019-6-2 09:41:00
categories: [python]
---

在任何一门编程语言中，函数都是非常重要的一个部分，当然python里也不例外。不过python里函数也会有一些额外的扩充，比如嵌套函数, 闭包和现在很多编程
语言都有的lambda表达式。

## python里正常的函数

先来看一下python里正常函数的样子:

```python
a = 1
def func(num):
    print(num+a)
```
函数里可以直接访问全局变量，但是如果要修改全局变量的话，则需要使用`global`关键字。

```python
a = 1
def func(num):
    global a
    a += 1
    print(num+a)
```

## 嵌套函数

python语言里支持嵌套函数，相当于在函数里像定义一个临时变量一样定义一个临时函数，它只能在函数内部访问。

```python
def func():
    print('in func')
    def func_innr():
        print('in func_innr')
    func_innr()

func()
```
这段代码的输出结果是：

```plain
in func
in func_innr
```
这就是嵌套函数的样子，其实就是定义了一个临时的函数。嵌套函数的作用有两个，一是保证内部函数的一些隐私不会曝露，二是可以提高函数运行效率。

```python
def connect_DB():
    def get_config():
        ...
        return username, passwd
    
    conn = connect(get_config())
    return conn
```
像这种写法，get_config()函数就无法在外部访问，从而不会让用户名和密码随意曝露。

```python
def sum(input_num):
    if not isinstance(input_num, int):
        raise Exception('input is not int')
    if input_num < 0:
        raise Exception('input must be bigger than 0')
        
    def inner_sum(input_sum):
        if input_sum == 1:
            return 1
        return input_sum + inner_sum(input_sum - 1)
    return inner_sum(input_num)
print(sum(5))
```
这段代码是完成一个累加求和的功能，通过定义一个内嵌函数完成，而外部函数只做一次参数检查，`inner_sum`里就不需要每次做参数类型检查，就会保证只让
核心的代码进行递归。

## 闭包

闭包和内嵌函数很类似，唯一的区别是，内嵌函数像函数一样仍然返回的是一个值，而闭包需要返回内嵌的函数。

```python
def func(a, b):
    def line(x):
        return a * x + b
    return line

line_res = func(2, 3)
print(line_res(1))
```
这是一个直线方程，通过外部函数传入斜率和截距，然后返回一个斜率和截距固定的函数。闭包通常和python里的装饰器一起配合使用。

## lambda表达式

lambda表达式也叫匿名函数，python里的lambda表达式的形式如下：
```python
lambda x : x+1
```
lambda表达式在python中有非常广泛的使用，对于一些只需要使用一次的临时函数，我们就不必要定义一个函数，而是直接使用lambda表达式代替。

```python
l = map(lambda x:x*2, [1,2,3,4,5])  # map返回的是一个可迭代的对象,需要使用list()转换成列表
print(list(l))
```