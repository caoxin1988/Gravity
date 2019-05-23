---
layout: post
title:  "python基础之set与dict比较"
author: dacaoxin
date:   2019-5-23 12:57:00
categories: [python]
---

前一篇写了列表(list)和元组(tuple)的区别，python还有另外两个很常用的集合(set)与字典(dict)也很常用。它们的优势是高效的查找和增加，删除, 这些
操作的时间复杂度均为O(1), 在有些场合，非常适用。

## 概念

什么是字典(dict), 在python中，字典是一系列*无序*的键值对的组合，字典的内容可以增加也可以改变。由于它是使用散列表实现的，所以相对于列表，字典
的增删改查操作更高效。

那集合(set)呢，和字典的实现非常类似，唯一的区别在于集合里的元素不是键值对，是单一的一个元素。

同列表和集合一样，python里字典和集合中的元素的类型都是混合型的，不一定必须要是同一类型元素。

## 推荐操作

使用字典有一个常用的场景就是通过键去查值，可以这样通过键来索引：

```python
d = {'a':1, 'b':2}
print(d['a'])   # 输出 1
```
但是如果我们不确定'c'这个键是否存在于字典d中，使用操作d[`c`]来索引就会报错:

```plain
KeyError                                  Traceback (most recent call last)
<ipython-input-5-05ba6e0488c7> in <module>()
----> 1 d['c']

KeyError: 'c'
```

所以更好的方法是使用get()方法，如下：

```python
val = d.get('c', 0)
```
这样即使键'c'不存在，也会返回一个默认值0，而不是报错。

另外一个常用的场景是，我们经常需要对字典进行遍历操作：

```python
d = {'a':1, 'b':2}

for key in d:   # 和for key in d.keys():这样写是一样的效果
    print(d[key])
```

集合的增加比较简单，直接使用add()方法就可以：
```python
s = {'a', 'b'}
s.add('c')
```

集合非常常用的场景是用来去重或者通过判断元素是否存在来避免重复操作(比如回溯算法中, 比如网页爬虫中对网址的去重)：

```python
# 对列表里的元素进行去重操作
l = [1, 2, 3, 1]
l_s= set(l)
```

```python
# 避免重复操作，利用了集合查询的高效性
l = [1, 2, 3, 1, 4]
s = set()
for index, item in enumerate(l):
    if item in s:
        continue
    else:
        # do what you want to do
        s.add(item)
```

## 性能

最上面我们说过，python中字典和集合的增删改查性能非常高，现在我们来举个例子说明，这也是字典和集合经常使用的场景, 假设我们后台存有市民的身份证号
和姓名信息，我们现在有一个需求是通过身份证号查人名，使用列表的实现如下(身份证号简写)：

```python
l = [
    (420213, 'zhangsan'),
    (420382, 'lisi'),
    (321962, 'wangwu')
]

def find_name(id_no):
    for id_num, name in l:
        if id_num == id_no:
            return name
        
    return None
```
这个实现实际上是需要遍历整个列表l，它的平均时间复杂度是O(n), 假设我们有100万用户，那查询效率可想而知有多差。但是如果采用字典存储的话，它的实现
如下:

```python
l = {
    420213: 'zhangsan',
    420382: 'lisi',
    321962: 'wangwu'
}

def find_name(id_no):
    return l.get(id_no, None)
```

字典查询的时间复杂度是O(1), 也就是说，无论是1个用户，还是100万用户，它的查找耗时更加稳定，显然这种实现方式要更加高效。
假设我们的需求变成，统计所有用户一共有多少个不同的名字, 即不重复的名字有多少个，先不管这个需求是否合理，如果用列表实现，如下：

```python
l = [
    (420213, 'zhangsan'),
    (420382, 'lisi'),
    (321962, 'wangwu')
]

def find_name_cnt(lis):
    unique_list = []
    for id_num, name in lis:
        if name not in unique_list:
            unique_list.append(name)
    return len(unique_list)
```
上面代码中，我们使用了一个列表来存储找到的不相同的名字，这里在从unique_list里查找是否有重复的时候，时间复杂度是O(n), 而最外层遍历整个列表时，
时间复杂度同样是O(n), 所以整个代码时间复杂度是O(n2)，效率很差，如果将unique_list换成集合呢？

```python
l = [
    (420213, 'zhangsan'),
    (420382, 'lisi'),
    (321962, 'wangwu')
]

def find_name_cnt(lis):
    unique_set = set()
    for id_num, name in lis:
        unique_set.add(name)            
    return len(unique_set)
```
因为集合中不会存在重复的元素，所以不需要查询，而且集合的实现也是散列表，它插入的时间复杂度同样是O(1)，所以这代代码的时间复杂度是O(n)，效率要高
出很多。

## 总结

字典和集合是两个非常重要的基础数据结果，它们大大提高了增删改查的效率，我们需要学会灵活使用它们。