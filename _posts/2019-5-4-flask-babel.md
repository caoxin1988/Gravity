---
layout: post
title:  "flask国际化插件flask-babel"
author: dacaoxin
date:   2019-5-4 19:48:00
categories: [python, flask]
---

获取本文的示例代码，点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/babel)

## 1. 安装使用flask-babel

flask插件flask-babel可以很方便的帮助我们实现国际化(i18n)。包括语言文字，时区，时间日期，数字，货币等。

使用pip安装flask-babel插件：

> $ pip install flask-babel

构建一个最简单的flask web应用程序:

```
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config')
    init_babel(app)

    return app

def init_babel(app):
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        return 'zh'

    @babel.timezoneselector
    def get_timezone():
        return 'UTC'
```
* config.py文件是flask框架将要使用的配置文件，在这里面可以做flask以及flask-babel等插件的配置
* 可以在config.py里通过设置BABEL_DEFAULT_LOCALE和BABEL_DEFAULT_TIMEZONE来指定babel默认使用的语言和时区
* 也可以使用localeselector和timezoneselector两个装饰器申明babel使用的默认语言以及时区选项, 需要注意的是，这两个装饰器的设置将会覆盖config.py里的设置
* localeselectort和timezoneselector装饰的函数，被调用一次之后就会缓存，可以在业务代码中使用*refresh()*清除缓存
* localeselectort和timezoneselector装饰的函数实质上是向Babel()对象中添加locale_selector_func和timezone_selector_func两个成员,然后由babel框架回调实现最终的设置

## 2. 语言文字翻译

flask-babel通过封装gettext()，ngettext()以及lazy_gettext()方法实现文字翻译功能。

> gettext和ngettext是为英文中单数和复数时名词后加s翻译到其它语言时使用的  
> lazy_gettext和gettext的区别在于，lazy_gettext只有在文字被使用的时候，才会被翻译

这里有有以下两个路由：

```
@app.route('/hello')
def hello():
    return gettext('hello, China')

@app.route('/')
def index():
    return render_template('index.html')
```

并且有模板文件index.html：

```
<!DOCTYPE html>
<h1>{ { _('Test Sample') }}</h1>
<h1>{ { _('Hello World!') }}</h1>
```

* 在模板文件中，也可以使用gettext(), 这里使用‘_’代替

利用flask-babel翻译文字步聚：

### 2.1 创建babel.cfg文件，并在里面加入:

```
[python: **.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
```

* 这段的主要意思是告诉*pybabel*从当前目录以及子目录下所有\.py文件和templates/及其子录下所有.html文件里抽取所有需要被翻译的文字，即被gettext(), ngettext()以及_()方法传入的文字

### 2.2 在项目根目录下，使用下面的命令生成messages.pot文件

> $ pybabel extract -F babel/babel.cfg -o babel/messages.pot app

* 这里要注意的是-F和-o后接的路径是运行*pybabel*命令的当前路径的相对路径，而最后的app这个参数则是告诉*pybabel*命令去哪里找\*\*.py和\*\*/templates/\*\*.html文件

如果还需要翻译lazy_gettext传入的语言，可以在上面命令基础上使用-k参数：

> $ pybabel extract -F babel/babel.cfg -k lazy_gettext -o babel/messages.pot app

在生成的messages.pot里，你可以看到所有使用类似于gettext()传递的参数，都出现在了msgid中。

### 2.3 创建文字对应的.po文件

使用命令

> $ pybabel init -i babel/messages.pot -d app/translations -l zh

会将中文翻译文件放在translations/zh/LC_MESSAGES下，命名为messages.po。

* 这里需要注意的是translations目录一定要和Flask对象app在同一级目录，否则翻译不会生效

### 2.4 翻译语言

在messages.po文件里，将每段文字的对应翻译放在msgstr中。

### 2.5 编译生成.mo文件

使用命令

> $ pybabel compile -d app/translations

编译.po文件生成相应的.mo文件，flask-babel最终也是使用.mo文件。在服务器中设置语言为zh,重启服务器，访问对应的url就可以看到中文网页了。

### 2.6 增量更新messages.po文件

如果代码中需要翻译的文字有变化，使用命令

> $ pybabel update -i messages.pot -d app/translations

可以在原来已经翻译好的.po文件基础上动态更改，而不会像*pybabel init*一样将之前辛苦翻译的.po文件内容全部丢掉。

## 3. 格式化时间日期

假如有如下路由

```
@app.route('/time')
def time():
    from flask_babel import format_datetime
    return format_datetime(datetime.now())
```

在语言为'zh'时，返回结果是：**2019年5月5日 下午10:56:04**  
当语言为'en'时，返回结果是：**May 5, 2019, 10:54:17 PM**

format_datetime()方法还可以带一个格式参数，用来定义输出的时间日期的样式，如'dd mm yyyy'。

## 4. 其它格式化

flask-babel还提供了一些其它常用的格式化方法，如

* format_currency: 格式化货币
* format_percent: 格式化百分比
* format_decimal: 格式化数字

等，可以自行尝试。
