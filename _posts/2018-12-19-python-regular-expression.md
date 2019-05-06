---
layout: post
title:  "python正则表达式总结"
subtitle: dacaoxin
author: dacaoxin
date:   2018-12-19 21:17:00
catalog:  true
tags:
    - python
---

python中常用正则表达式总结：

## 1. 模式

\w : 匹配数字、字母、下划线中任意一个字符， 相当于 [a-zA-Z0-9_]  
\W : 匹配非数字、字母、下划线中的任意字符，相当于 [^a-zA-Z0-9_]  
\d : 匹配一个数字， 相当于 [0-9]  
\D : 匹配非数字,相当于 [^0-9]  
\s : 匹配任意空白字符， 相当于 [ \t\n\r\f\v]  
\S : 匹配非空白字符，相当于 [^ \t\n\r\f\v]

(..) : 分组，默认为捕获，即被分组的内容可以被单独取出，默认每个分组有个索引，从 1 开始，按照"("的顺序决定索引值, 可以和后面的\number配合使用，也经常用在re.search()和re.match()返回的Match对象中  

\number : 可以上面的(..)分组配合使用，比如

```
    re.compile(r'(python)123\1')
    \1就代表python这个字符串，需要记住的是，一般使用\number时，字符串最好加个r标识，否则\有可能会被误识别为是转义符
```

\* : 匹配前一个元字符或模式0到多次   
\+ : 匹配前一个元字符或模式1到多次  
? : 匹配前一个元字符或模式0或1次
{n, m} : 匹配次数  
. : 匹配任意字符(不包含换行符)  

## 2. 正则表达式匹配方法

* re.findall()

    返回的是列表

* re.match()

    从字符串的开头开始匹配，返回值是一个Match对象，可以使用groups(), group(0), group(1)等取值

* re.search()

    和match()类似，只不过它不是从字符串的头开始匹配，而是任意位置

* re.sub()

    re.sub()的高级用法如下：

```
    def convert(value):
        matched = value.group()
        return '!!' + matched + '!!'

    re.sub('java', convert, 'pythonjavapythonjava')
```

## 3. group()方法

    group相关的方法有groups(), group(), group(1) ...

```
    s = 'lifes is short, i use python'
    r = re.match('life([a-z ]*)short.*(python)', s)
    print(r.group())
    print(r.group(0))
    print(r.group(1))
    print(r.group(2))
    print(r.group(0, 1, 2))
    print(r.groups())
```

    group()和group(0)返回的都是整个正则表达式的结果，group()的参数从1开始，表示每个分组的结果. groups()表示返回所有的匹配的分结果， 上面返回结果是：

```
    'life is short, i use python'
    'life is short, i use python'
    ' is'
    'python'
    ('life is short, i use python', ' is', 'python')
    (' is', 'python')
```