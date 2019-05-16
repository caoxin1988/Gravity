---
layout: post
title:  "flask-appbuilder使用"
author: dacaoxin
date:   2019-4-28 10:48:00
categories: [python, flask]
---


## 1. flask-appbuilder环境

### 1.1 环境与依赖包

```
	$ pipenv --python 3.7
	$ pipenv shell
	$ pipenv install flask-appbuilder
```

安装flask-appbuilder包过程中，会同时安装一些别的包，比如flask, flask-babel等之类的包。

### 1.2 构建

在flask-appbuilder 2.2.x版本之后，fabmanager命令将会被丢弃，将可以使用flask fab [commands]代替。这里我们仍将使用fabmanager命令。

```
$ fabmanager create-app  ## 之后输入你想要的项目文件夹名, 并会提示你选择需要对接的数据库引擎
  Your new app name: first_app
  Your engine type, SQLAlchemy or MongoEngine [SQLAlchemy]:
  Downloaded the skeleton app, good coding!
$ cd first_app
$ flask fab create-admin
  Username [admin]:
  User first name [admin]:
  User last name [user]:
  Email [admin@fab.org]:
  Password:
  Repeat for confirmation:
```

之后将会把flask-appbuilder的框架代码从[这里](https://github.com/dpgaspar/Flask-AppBuilder-Skeleton.git)下载到刚才填写的first_app这个目录下。

### 1.3 运行

使用如下命令运行这个demo:

> python run.py

或者使用如下命令运行：

>$ export FLASK_APP=app  
 $ python -m flask run


## 2. flask-appbuilder常用demo搭建
 
### 2.1 flask-appbuilder框架结果

使用上面的命令自动构建好flask-appbuilder初始框架之后,在first_app文件夹(这个文件夹是刚才输入的app name的名字)下结构如下：

![appbuilder](/images/appbuilder/appbuilder_tree.png)

* app/__init__.py是正个项目的入口文件，里面初始化了flask和flask-appbuilder实例
* app/templates/下存放整个项目的所有前端使用Jinja2渲染的模板文件
* app/translations/下存放的是基于flask-babel使用的多语言翻译文件
* app/views.py和app/models.py文件里可以添加自己需要实现的业务代码
* babel/下存放flask-babel插件使用的配置文件(babel.cfg)以及需要被翻译的文字内容(messages.pot)
* app.db是一个sqlite3的数据库文件，默认代码中SQLAlchemy使有的数据库都存放在这个文件里，比如登际的用户名和密码之类的
* config.py是flask使用的默认配置文件，所有flask插件(如flask-babel, flask-appbuilder)使用的配置都在这个文件里

使用flask-appbuilder构建项目，最主要的业务代码都是基于views.py和models.py来做扩展，使用flask-appbuilder封装好的类来快速实现业务逻辑。

### 2.2 BaseView类

通过实现一个继承自BaseView的类，flask-appbuilder框架可以方便的帮我们注册一个flask的Blueprint(蓝图)。通过appbuilder的add_view_no_menu()和add_view()方法将使用BaseView类实现的url注册到flask框架中。

> add_view_no_menu()和add_view()两个方法的区别就在于，add_view_no_menu()在将url注册到flask中的同时，还会利用flask-appbuilder框架帮我们在前端网面上实现一个菜单。

```
class MyView(BaseView):

    @expose('/method1/')
    def method1(self):
        return 'Hello'

    @expose('/method2/<string:param1>')
    @has_access
    def method2(self, param1):
        param1 = 'Hello %s' % (param1)
        return param1

appbuilder.add_view(MyView, 'Method1', category='My View')
appbuilder.add_link('Method2', href='/myview/method2/john', category='My View')
```

* add_link()方法可以实现二级菜单的注册
* expose()方法相当于flask中在Blueprint下注册子url
* has_access装饰器可以标明这些方法只有登陆之后才有权访问

通过继承BaseView类，可以方便快捷的在flask下通过Blueprint实现url，并且可以自由的通过模版渲染我们需要的页面样子和内容。

### 2.3 FormView

使用flask-appbuilder框架里的DynamicForm类和SimpleFormView类可以方便的构建表单的页面以及表单的读写提交功能。

```
class MyForm(DynamicForm):
    field1 = StringField(('Field1'),
        description=('Your field number one!'),
        validators = [DataRequired()], widget=BS3TextFieldWidget())
    field2 = StringField(('Field2'),
        description=('Your field number two!'), widget=BS3TextFieldWidget())

class MyFormView(SimpleFormView):
    form = MyForm
    form_title = 'This is my first form view'
    message1 = 'My form submitted'

    def form_get(self, form):
        form.field1.data = 'This was prefilled'

    def form_post(self, form):
        # post process form
        flash(self.message1, 'info')

appbuilder.add_view(MyFormView, "My form View", icon="fa-group", label=_('My form View'),
                     category="My Forms", category_icon="fa-cogs")
```

这段代码之后的效果图如下：

![formview](/images/appbuilder/formview.png)

### 2.3 ModelView

flask-appbuilder框架通过ModelView类提供了非常方便的页面操作和数据库结合的功能。同时ModelView类定义了很方便的对数据库增删改查以及相应操作的页面展示的功能。

```
class Contact(Model):
    id = Column(Integer, primary_key=True)
    name =  Column(String(150), unique = True, nullable=False)
    address =  Column(String(564), default='Street ')
    birthday = Column(Date)
    personal_phone = Column(String(20))
    personal_cellphone = Column(String(20))
    contact_group_id = Column(Integer, ForeignKey('contact_group.id'))
    contact_group = relationship("ContactGroup")

    def __repr__(self):
        return self.name

class ContactModelView(ModelView):
    datamodel = SQLAInterface(Contact)

    label_columns = {'contact_group':'Contacts Group'}
    list_columns = ['name','personal_cellphone','birthday','contact_group']

    show_fieldsets = [
                        (
                            'Summary',
                            {'fields': ['name', 'address', 'contact_group']}
                        ),
                        (
                            'Personal Info',
                            {'fields': ['birthday', 'personal_phone', 'personal_cellphone'], 'expanded': False}
                        ),
                     ]

appbuilder.add_view(
    ContactModelView,
    "List Contacts",
    icon = "fa-envelope",
    category = "Contacts"
)
```

* list_columns定义了使用list/这个url访问时，前面页面要展示的内容
* show_fieldsets定义了使用show/这个url访问时，前面页面要展示的内容以及分组展示方式。show/这个url实际上就是list里每一项的Show Contact时请求的url。

上一段代码的效果图如下：

![modelview](/images/appbuilder/modelview.png)

### 2.4 REST API

flask-appbuilder框架通过BaseApi类可以快速方便的构建restful api。

```
class ExampleApi(BaseApi):

    @expose('/greeting')
    def greetingdd(self):
       return self.response(200, message='hello greeting')


appbuilder.add_api(ExampleApi)
```

之后，使用*curl /api/v1/exampleapi/greeting*可以访问这个restful api

## 3. 多语言支持

flask-appbuilder通过集成flask-babel来实现多语言支持，关于flask-babel插件，可以点击[这里](https://caoxin1988.github.io/python/flask/2019/05/04/flask-babel.html)查看。
flask-appbuilder里对于多语言命令又做了一层封装，和单独使用flask-babel略有差别，具体使用方法如下:

在babel文件夹下添加文件babel.cfg，并添加以下内容：

```
[python: **.py]
[jinja2: **/templates/**.html]
encoding = utf-8
```

建立不同语言翻译的初始文件：

```
$ pybabel init -i ./babel/messages.pot -d app/translations -l zh
```

执行后会在translations目录下创建zh/LC_MESSAGES/messages.po文件。接着执行

```
$ flask fab babel-extract
```

然后更改messages.po文件里英语对应的翻译：

```
$ flask fab babel-compile
```

之后会在messages.po文件同级目录下生成messages.mo文件。这个文件将最终被flask代码使用。


在代码和templates中，使用gettext()和lazy_gettext()方法来进行语言的转换。如：

```
@app.route('/trans/')
def translate(num=None):
    if num is None:
        return gettext(u'No users')
    return ngettext(u'%(num)d user', u'%(num)d users', num)
```

lazy_getext()和gettext()的区别在于，lazy_gettext()所转换的文字，是在真正被使用的时候才会发生转换，如：

```
from flask_babel import lazy_gettext
hello = lazy_gettext(u'Hello World')
 
@app.route('/lazy')
def lazy():
    return unicode(hello)
```
