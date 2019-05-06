---
layout: post
title:  "Android切换activity动画"
subtitle: dacaoxin
author: dacaoxin
date:   2017-7-9 14:23:00
catalog:  true
tags:
    - rom
    - android
    - activity
---

我们在写App的时候都会在AndroidManifest.xml里为每个application通过android:theme属性来设置app的样式。有时候我们会在自己的代码里通过继承Theme，通过修改Theme
里的属性值来定制自己的App主题样式。如果没有做过任何属性的重写，就会使用Android设备ROM里默认的Theme的样式。

那可能会有人会问，Android设备里默认的Theme保存在哪里呢？对，就是在framework-res.apk里。在AOSP的代码里就是framework/base/core/res/values/themes.xml。在theme.xml
里定义了很多种属性，其中有一个比较有意思的是android:windowAnimationStyle：


[framework/base/core/res/values/themes.xml]

	<resources>
		<style name="Theme">
		... ...
		
			<item name="android:windowAnimationStyle">@android:style/Animation.Activity</item>
		
		... ...
		</style>
		
		... ...
	</resources>
	
Animation.Activity的定义如下：


[framework/base/core/res/values/styles.xml]

	<resources>
		<style name="Animation.Activity">
			<item name="activityOpenEnterAnimation">@anim/activity_open_enter</item>
			<item name="activityOpenExitAnimation">@anim/activity_open_exit</item>
			<item name="activityCloseEnterAnimation">@anim/activity_close_enter</item>
			<item name="activityCloseExitAnimation">@anim/activity_close_exit</item>
			<item name="taskOpenEnterAnimation">@anim/task_open_enter</item>
			<item name="taskOpenExitAnimation">@anim/task_open_exit</item>
			<item name="taskCloseEnterAnimation">@anim/task_close_enter</item>
			<item name="taskCloseExitAnimation">@anim/task_close_exit</item>
			<item name="taskToFrontEnterAnimation">@anim/task_open_enter</item>
			<item name="taskToFrontExitAnimation">@anim/task_open_exit</item>
			<item name="taskToBackEnterAnimation">@anim/task_close_enter</item>
			<item name="taskToBackExitAnimation">@anim/task_close_exit</item>
			<item name="wallpaperOpenEnterAnimation">@anim/wallpaper_open_enter</item>
			<item name="wallpaperOpenExitAnimation">@anim/wallpaper_open_exit</item>
			<item name="wallpaperCloseEnterAnimation">@anim/wallpaper_close_enter</item>
			<item name="wallpaperCloseExitAnimation">@anim/wallpaper_close_exit</item>
			<item name="wallpaperIntraOpenEnterAnimation">@anim/wallpaper_intra_open_enter</item>
			<item name="wallpaperIntraOpenExitAnimation">@anim/wallpaper_intra_open_exit</item>
			<item name="wallpaperIntraCloseEnterAnimation">@anim/wallpaper_intra_close_enter</item>
			<item name="wallpaperIntraCloseExitAnimation">@anim/wallpaper_intra_close_exit</item>
			<item name="fragmentOpenEnterAnimation">@animator/fragment_open_enter</item>
			<item name="fragmentOpenExitAnimation">@animator/fragment_open_exit</item>
			<item name="fragmentCloseEnterAnimation">@animator/fragment_close_enter</item>
			<item name="fragmentCloseExitAnimation">@animator/fragment_close_exit</item>
			<item name="fragmentFadeEnterAnimation">@animator/fragment_fade_enter</item>
			<item name="fragmentFadeExitAnimation">@animator/fragment_fade_exit</item>
		</style>
		
		... ...
	</resources>
	
Animation.Activity里定义了几个重要有属性：

* activityOpenEnterAnimation, activityOpenExitAnimation, activityCloseEnterAnimation,activityCloseExitAnimation 表示activity打开和退出时的动画效果
* taskOpenEnterAnimation，taskOpenExitAnimation，taskCloseEnterAnimation，taskToFrontEnterAnimation，taskToFrontExitAnimation，taskToBackEnterAnimation，taskToBackExitAnimation
表示新建/退出/移动 task时的动画效果。

前几天遇到过一个问题，因为修改了电视的屏幕密度参数ro.sf.lcd_density，导致所有打开一个在新的task里的activity时，切换效果变了。后面发现taskOpenEnterAnimation等这几个动画在anim, anim-land, anim-sw720dp中各有一份。
并且不同的文件夹里定义的动画效果是不同的，这个时候突然明白问题的原因了，应该是修改了屏幕密度导致选择了不同的动画资源，所以task的切换效果变了。

当然themes.xml里还定义了各种各样的效果，有兴趣可以自行研究。