---
layout: post
title:  "Source Insight 4.0"
subtitle: dacaoxin
author: dacaoxin
date:   2017-2-23 16:06:00
catalog:  true
tags:
    - tools
---

一直习惯于用Source Insight来阅读代码，特别喜欢那个预览窗口和左侧的TAGS窗口，觉得这样读代码很容易整体把握。今天偶然间发现Source Insight4.0发布了，然后去官网看了一下，多了很多很炫的功能，
让这个IDE一下子看上去变成了一个新时代的产品，也集成了当下很多主流IDE的新功能，很好用。这里简单介绍一下。先贴个图，流下口水喽。
![sourceinsight 4.0](/images/sourceinsight/preview.jpg)

## 1 安装

在[这里](https://www.sourceinsight.com/download/)可以下载到最新的Source Insight 4.0版本，点[这里](https://www.sourceinsight.com/#features)可以查看新版软件的新功能。

* 需要注意的是，Source Insight 4.0好像不支持中文路径，不管是配置文件，工程文件，还是安装目录，如果有中文中路径就会有问题。

## 2 Source Insight 4.0新功能使用

这里简单介绍一下常用的几个新功能的使用方法。

### 2.1 更改主题

作为一个linux工程师，我比较喜欢那种暗暗的配色，显得很有hacker范，所以我非常喜欢Source Insight 4.0里提供的这个功能。更改方法如下：

	Options > Visual Theme > theme name
	
当然这里也可以根据自己的喜好来配置颜色。

### 2.2 代码折叠

很多时候代码里的函数很长，然而我们的显示器的大小又有限，所以代码折叠功能就特别好用，它可以帮助我们更好的整体把握代码，点击这里就可以折叠或打开代码：

![代码折叠](/images/sourceinsight/collaping.jpg)

### 2.3 代码比较

在做开发和debug的过程中，经常会使用到代码比较工具，Source Insight 4.0集成了文件比较和文件夹比较工具，相当的赞。

* 文件比较

> Tools > Compare File

![文件比较](/images/sourceinsight/file_compare.jpg)

* 文件夹比较

> Tools > Directory Compare

![文件夹比较](/images/sourceinsight/dir_compare.jpg)

个人感觉这个文件夹比较功能不好用，不如beyond compare好用。

### 2.4 引用自动高亮

这个功能非常实用，鼠标放在一个变量或函数上，文件里引用改变量或函数的地方全部会高亮，让我们一眼就能看得清清楚楚。

![引用自动高亮](/images/sourceinsight/highting.jpg)

这个功能默认并不是打开的，需要做如下两步配置：

* 点击 Options > File Type Options, 勾选"Highlight ref­erences to selected symbol"
* 点击 Options > Style Properties, 找到并编辑 "Reference Highlight"，这里还可以配置高亮的样式。
