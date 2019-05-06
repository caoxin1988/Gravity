---
layout: post
title:  "Android Studio编写系统APP"
subtitle: dacaoxin
author: dacaoxin
date:   2017-6-14 21:59:00
catalog:  true
tags:
    - tools
    - android
    - app
---

之前我们工作中都是使用Eclipse来编写system app, 因为Eclipse能够很方便的引用我们自己ROM的framework.jar。而现在Android Studio正在变得越来越流行,
几乎所有的APP开发者都开始使用Android Studio, 那我们如何才能够在AS里调用自己的framework.jar而不是SDK里的呢。

当我们需要写一些系统内置的APP时，比如Launcher, Setting之类的，它们经常会使用到一些隐藏的API，而这些API在SDK里是找不到的，或者使用一些我们自己ROM里
编写的接口，这时候我们就需要引用我们自己的framework.jar, 否则Android Studio里是编译不过的。

下面就来介绍一下如何在AS里引用自己的framework.jar编写一个系统APK:

* 在源码的out目录下找到我们自己的framework.jar, 它在

> out/target/common/obj/JAVA_LIBRARIES/framework_intermediates/classes.jar

特别要注意的是，并不是

> out/target/product/your_target/system/framework/framework.jar

第一个是完整的java library, 而第二个jar包更像是SDK里的framework.jar

* 将classes.jar拷到/projectpath/app/libs/下，并重命名为framework.jar

* 像在Ecplise里的extended library一样引用framework.jar, 在/projectpath/app/build.gradle的dependencies添加

	dependencies {
		// 第一句一定要删掉，否则app打开后会因找不到activity而直接crash
		//compile fileTree(dir: 'libs', include: ['*.jar'])
		androidTestCompile('com.android.support.test.espresso:espresso-core:2.2.2', {
			exclude group: 'com.android.support', module: 'support-annotations'
		})
		... ...
		testCompile 'junit:junit:4.12'
		provided files('libs/framework.jar')	// 添加这句, provided表示只引用，而不编译到APK里去
	}
	
* gradle打包时，也需要指定我们自己的framework.jar的位置，在/projectpath/app/build.gradle的buildscript里添加

	gradle.projectsEvaluated {
        tasks.withType(JavaCompile) {
            options.compilerArgs.add('-Xbootclasspath/p:app/libs/framework.jar')
        }
    }
	
> 注意，这里app目录是一个AS工程的一个module

完成上面这些之后，使用gradle编译的apk使用的就是我们自己的framework.jar里的API。但是这里还有一个小问题，就是你会发现如果代码里
调用我们自己添加的API接口时，AS里提示没有这个接口，会显示这里有语法错误。但是事实上，gradle编译的时候确实可以编译通过，并生成可以运行的APK。
这是因为Android Studio里永远会将SDK作为第一个语法解析的jar包。

我们可以将/projectpath/app/app.iml里<orderEntry>下面的

	<orderEntry type="jdk" jdkName="Android API 23 Platform" jdkType="Android SDK" />
	
放到最后去，也就是在我们自己的framework.jar之后。然后Android Studio就不会有语法错误提示了。

> 注意，这样修改之后，只有java文件不会提示语法错误，kotlin文件里仍然会提示语法错误，这个暂时还没有找到解决办法



	
