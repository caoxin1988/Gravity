---
layout: post
title:  "macos中优雅使用terminal"
subtitle: dacaoxin
author: dacaoxin
date:   2019-4-26 19:43:00
catalog:  true
tags:
    - macos
---

## 1. 下载，安装iTerm2 

iTerm2是一个非常强大的terminal软件，使用iTerm2代替macos自带的难用的erminal。点击[此处](https://www.iterm2.com/downloads.html)下载并安装iTerm2。

### 1.1. 设置iTerm2配色方案

我比较喜欢Dracula配色主题，网址是[Dracula](https://draculatheme.com/iterm/)。这个网站上有下载和设置方式。按步骤来就可以了。

### 1.2. 设置Monaco字体补丁

点击[此处](https://github.com/supermarin/powerline-fonts/blob/bfcb152306902c09b62be6e4a5eec7763e46d62d/Monaco/Monaco%20for%20Powerline.otf)下载Monaco字体补丁，并双击安装。

安装完成后，点击iTerm2左上脚【iTerm2】 -> 【Preferences...】-> 【Profiles】-> 【Text】，设置字体为'12pt Monaco For Powerline'，如图：

![Monaco字体](/images/terminal/monaco.png)


## 2. Oh My Zsh

### 2.1 安装Oh My Zsh

Oh My Zsh在github上地址是：[Oh My Zsh](https://github.com/robbyrussell/oh-my-zsh)。可以直接在iTerm2中直接使用:

> sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"

或

> sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)"

两条中的任意一条命令进行安装。

### 2.2 配置~/.zshrc

安装好Oh My Zsh之后，在~/.zshrc文件开头添加以下几项:

```
	source ~/.bash_profile
	DEFAULT_USER="xxx"  # 这里的xxx替换成你自己的用户名
	plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
```

在~/.zshrc里将ZSH_THEME的值更改为"agnoster", 则可以选择主题为agnoster




