---
layout: post
title:  "flask用户会话插件flask-login"
author: dacaoxin
date:   2019-5-7 23:48:00
categories: [python, flask]
---

使用flask做web应用开发时，用户登录以及会话管理一定是个必须的功能。

## 1. 使用session保持用户状态

由于http协议的无状态性，在flask里使用session实现请求间信息共享功能。代码如下：

```
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        if request.form['user'] == 'admin':
            session['user'] = request.form['user']
            return 'admin login successfully'
        else:
            return 'no such user'

    if 'user' in session:
        response = make_response('hello {}'.format(session['user']), 200)
        return response
    else:
        title = request.args.get('title', 'Default')
        return render_template('login.html', title=title)

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('login'))
```
可以看到，‘admin'登陆时，会使用session来保存它的登陆状态。之后的/login请求，会从session里拿到登陆状态，就不会再出现输入用户名的那个登陆表单
了。使用session时，需要在config.py里设置密钥*SECRET_KEY = '123456'*,否则会报异常。


更常用的一种操作是，有很多页面必须要在用户登陆之后才有能访问和操作，而在每个视图函数里都加上上面那段判断session是否存在就会显得很繁琐，并且这样
代码也不简洁。这个时候，就需要一个装饰器来实现。

```
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not 'user' in session:
            abort(401)
        return view_func(*args, **kwargs)

    return wrapper

@app.route('/admin')
@login_required
def admin():
    return 'admin allowed'
```
使用@login_required装饰过视图函数admin()之后，只有登陆过的用户才有权限访问/admin这个url了。

获取示例代码，点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/session)


## 2. flask-login插件

如果你觉得上面写起来还是很费劲，那么flask-login插件可以帮到你。当然flask-login的功能远比上面更全面。

### 2.1 安装

> $ pip install flask-login

创建flask-login实例:

```
from flask import Flask
from flask_login import LoginManager
 
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

# 如果未登陆的用户访问了一个只有登际用户才能访问的Url, 即被@login_required修饰的url
# 那这次访问会被重定向到login_view定义的这个视图函数里，同时闪现由login_message定义的错误消息
# 并且会在Url后添加?next=xxx，以便用户名和密码验证成功后跳转
login_manager.login_view = AUTH_BLUEPRINT + '.login'
login_manager.login_message = 'Unauthorized User'
```

使用flask-login时，也需要配置SECRET_KEY，否则也会报错。

### 2.2 实现用户类

使用Flask-Login插件之前，最重要的就是要定义User类，Flask-Login规定User类必须要实现三个属性和一个方法：

* is_authenicated属性
* is_active属性
* is_anonymous属性
* get_id()方法

Flask-Login提供了一个很方便的方式完成这些，继承UserMixin类

```
from flask_login import UserMixin

class User(UserMixin):

    def __init__(self):
        pass
```

### 2.3 加载用户

在开始使用flask-login之前，需要实现一个用户对象加载的方法。这里先用列表和字典来存储用户名和密码，后面关于flask-sqlalchemy的文章中，会在这里
添加数据库。

```
users = [
    {'username': 'tom', 'password': '111111'},
    {'username': 'admin', 'password': '123456'}
]

def query_user(username):
    for user in users:
        if username == user['username']:
            return user
    return None


@login_manager.user_loader
def load_user(username):
    if query_user(username):
        cur_user = User()
        cur_user.id = username

        return cur_user
```

通过@login_manager.user_loader装饰器装饰的方法是一个回调函数。当每次有被@login_required等装饰的请求url到达时，Flask-Login都会从
Session中寻找”user_id”的值，如果找到的话，就会用这个”user_id”值来调用此回调函数load_user检查用户是否存在，并构建一个用户类对象

### 2.4 登入登出

在用户登陆的视图函数中，验证完username和password之后，使用login_user()使用上面实现的user对象的get_id()方法将user的id属性设置到session
的‘user_id’里。

同理，登出时，使用logout_user()帮忙清理user的session。

```
@auth_blueprint.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = query_user(username)

        if user and request.form.get('password') == user['password']:
            curr_user = User()
            curr_user.id = username     # 最后会放到session['user_id']中

            login_user(curr_user)

            return redirect(url_for(AUTH_BLUEPRINT + '.index'))

        flash('Wrong username or password!')

    return render_template('login.html', login=AUTH_BLUEPRINT + '.login')

@auth_blueprint.route('/home')
@login_required
def home():
    return render_template('hello.html')
```

home()方法使用@login_required装饰器修饰之后，之个url就必须只有登陆的用户才有权限访问。

### 2.5 自定义未授权访问方法

之前通过*login_manager.login_view = AUTH_BLUEPRINT + '.login'*可以让访问需要登陆用户才能访问的url时，跳转到指定的url中。
如果我们想自定义处理方法，可以使用@login_manager.unauthorized_handler这个装饰器

```
@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'
```

获取示例代码，点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/login)。更多关于flask-login的使用，可以查看
(官方文档)[https://flask-login.readthedocs.io/en/latest/]