---
layout: post
title:  "Ubuntu16.04上编译Androidd6.0"
subtitle: dacaoxin
author: dacaoxin
date:   2016-12-26 23:30:00
catalog:  true
tags:
    - tools
---
前两天突然抽风，把公司的编译机器从Ubuntu14.04升级到了Ubuntu16.04。然后本来好好的代码无法编译成功了，经过了一两天的google和尝试，现在终于可以编过了， 这里记录一下做的修改。

# 一. Android 6.0(Marshmallow)

## 1. 安装jdk7    

    sudo add-apt-repository ppa:openjdk-r/ppa  
    sudo apt-get update  
    sudo apt-get install openjdk-7-jdk 

## 2. 安装依赖package

安装下面的package, ubuntu16.04和ubuntu14.04上可能有点不一样

    sudo apt-get install -y git flex bison gperf build-essential libncurses5-dev:i386 
    sudo apt-get install libx11-dev:i386 libreadline6-dev:i386 libgl1-mesa-dev g++-multilib 
    sudo apt-get install tofrodos python-markdown libxml2-utils xsltproc     zlib1g-dev:i386 
    sudo apt-get install dpkg-dev libsdl1.2-dev libesd0-dev
    sudo apt-get install git-core gnupg flex bison gperf build-essential  
    sudo apt-get install zip curl zlib1g-dev gcc-multilib g++-multilib 
    sudo apt-get install libc6-dev-i386 
    sudo apt-get install lib32ncurses5-dev x11proto-core-dev libx11-dev 
    sudo apt-get install lib32z-dev ccache
    sudo apt-get install libgl1-mesa-dev libxml2-utils xsltproc unzip m4
    

## 3. 修改clang

修改art/build/Android.common_build.mk


    ifneq ($(WITHOUT_HOST_CLANG), true)
       # By default, host builds use clang for better warnings.
       ART_HOST_CLANG := true
    endif

改为

    ifeq ($(WITHOUT_HOST_CLANG), false)
       # By default, host builds use clang for better warnings.
       ART_HOST_CLANG := true
    endif

## 4. 使能jack server

在ubuntu16.04上可能必须要用jack server, 所以保持~/.jack内容如下

    # Server settings
    SERVER=true
    SERVER_PORT_SERVICE=8072
    SERVER_PORT_ADMIN=8073
    SERVER_COUNT=1
    SERVER_NB_COMPILE=2
    SERVER_TIMEOUT=60
    SERVER_LOG=${SERVER_LOG:=$SERVER_DIR/jack-$SERVER_PORT_SERVICE.log}
    JACK_VM_COMMAND=${JACK_VM_COMMAND:=java}
    # Internal, do not touch
    SETTING_VERSION=2
    
# 二.  Android 4.4(KitKat)

## 1. 安装jdk1.6

Android4.4使用的jdk版本是1.6，所以自己安装openjdk-6, 也可以去Oracle官网下载后自己解压到电脑上。

## 2. 修改main.mk

Android4.4默认最高只支持make 4.0, Ubuntu16.04默认安装的make是4.1版本，所以做如下修改:

    ifeq (,$(findstring CYGWIN,$(shell uname -sm)))
    ifeq (0,$(shell expr $$(echo $(MAKE_VERSION) | sed "s/[^0-9\.].*//") = 3.81))
    ifeq (0,$(shell expr $$(echo $(MAKE_VERSION) | sed "s/[^0-9\.].*//") = 3.82))
    ifeq (0,$(shell expr $$(echo $(MAKE_VERSION) | sed "s/[^0-9\.].*//") = 4.0))
    $(warning ********************************************************************************)
    $(warning *  You are using version $(MAKE_VERSION) of make.)
    $(warning *  Android can only be built by versions 3.81 and 3.82.)
    $(warning *  see https://source.android.com/source/download.html)
    $(warning ********************************************************************************)
    $(error stopping)
    endif
    endif
    endif
    endif

更改为：  
    
    ifeq (,$(findstring CYGWIN,$(shell uname -sm)))
    ifeq (0,$(shell expr $$(echo $(MAKE_VERSION) | sed "s/[^0-9\.].*//") = 3.81))
    ifeq (0,$(shell expr $$(echo $(MAKE_VERSION) | sed "s/[^0-9\.].*//") = 3.82))
    ifeq (0,$(shell expr $$(echo $(MAKE_VERSION) | sed "s/[^0-9\.].*//") = 4.1))
    $(warning ********************************************************************************)
    $(warning *  You are using version $(MAKE_VERSION) of make.)
    $(warning *  Android can only be built by versions 3.81 and 3.82.)
    $(warning *  see https://source.android.com/source/download.html)
    $(warning ********************************************************************************)
    $(error stopping)
    endif
    endif
    endif
    endif
