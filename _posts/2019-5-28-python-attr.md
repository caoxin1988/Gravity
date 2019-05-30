---
layout: post
title:  "python基础之getattr, __getattr__, __getattribute__以及__get__区别"
author: dacaoxin
date:   2019-5-28 22:37:00
categories: [python]
---

在阅读很多优秀的python框架代码时，getattr(), \__getattr__(), \__getattribute__()和\__get__()这几个方法都是很常见的，它们都是在什么时候
被调用呢，用处又是什么，然后它们之前有哪些关联呢。下面来通过例子分析一下。

## getattr()

和另外三个方法都是魔法函数不同的是，getattr()是python内置的一个函数，它可以用来获取对象的属性和方法。例子如下:

```python
class A():
    a = 5
    def __init__(self, x):
        self.x = x

    def hello(self):
        return 'hello func'

a = A(10)

print(getattr(a, 'x'))  #相当于a.x
print(getattr(a, 'y', 20))  #相当于a.y，因为a.y并不存在，所以返回第三个参数作为默认值
print(getattr(a, 'hello')())  # 相当于a.hello()

print(getattr(A, 'a'))  # 相当于A.a
```
这段代码的输出结果是：

```plain
10
20
hello func
5
```
可以看出，getattr()可以用来获取对像的属性和方法，需要注意的是，如果通过getattr()来尝试获取对象里并不存在的属性时没有添加第三个默认值，代码会
报错，如下所示:

```python
print(getattr(a, 'y'))
```
运行会报异常提示找不到属于y:

```plain
Traceback (most recent call last):
  File "app/test.py", line 32, in <module>
    print(getattr(a, 'y'))
AttributeError: 'A' object has no attribute 'y'
```

## \__getattr__()与\__getattribute__()

这两个是类对象的魔法函数，在访问对象属性的时候会被调用，但是两者之间也有一点区别, 我们通过代码来看一下:

```python
class A(object):
  def __init__(self, x):
    self.x = x

  def hello(self):
    return 'hello func'

  def __getattr__(self, item):
    print('in __getattr__')
    return 100

  def __getattribute__(self, item):
    print('in __getattribute__')
    return super(A, self).__getattribute__(item)

a = A(10)
print(a.x)
print(a.y)
```
运行代码，得到下面输出:

```plain
in __getattribute__
10
in __getattribute__
in __getattr__
100
```
可以看出，在获到对象属性时，\__getattribute__()是一定会被调用的，无论属性存不存在，首先都会调用这个魔法方法。
如果调用像`a.y`这种不存在的对象时，调用\__getattribute__()找不到`y`这个属性，就会再调用\__getattr__()这个魔法方法，可以通过在这个方法里实
来设置属性不存在时的默认值。使用上面的getattr()方法获取属性时，也是同样的调用关系，只不过只有在getattr()带第三个参数作为默认值时，才会调用
\__getattr__()方法。

## \__get__()

\__get__()方法是描述符方法之一，和他经常配套使用的是\__set__()方法，通过描述符，可以将访问对象属性转变为调用描述符方法。这在ORM中被经常使用，
可以通过描述符方法进行参数格式验证。

```python
import random

class Die(object):
    def __init__(self, sides=6):
        self.sides = sides

    def __get__(self, instance, owner):
        print('Die __get__()')
        return int(random.random() * self.sides) + 1

    def __set__(self, instance, value):
        print('Die __set__()')

class Game(object):
    d6 = Die()
    d10 = Die(sides=10)
    d20 = Die(sides=20)

game = Game()
print(game.d6)

game.d6 = 10
```
这段代码的输出结果是:

```plain
Die __get__()
5
Die __set__()
```
这就是描述符的作用, 使用描述符可以让我们在获取或者给对象赋值时对数据值进行一些特殊的加工和处理。python里经常使用的`@property`装饰器其实就是
通过描述符的方式实现的。
当然关于描述符，我们还需要知道，如果一个类仅仅实现了`__get__()`方法，那么这个类被称为非数据描述符；如果一个类实现在`__get__()`并且还实现在
`__set__()`和`__del__()`中的一个，这个类就被称为数据描述符。
