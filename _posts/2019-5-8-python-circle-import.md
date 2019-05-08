---
layout: post
title:  "python中import包时产生的循环依赖"
author: dacaoxin
date:   2019-5-8 23:48:00
categories: [python]
---

使用python写一个稍微大一点的工程时，经常会遇到循环import，即cicular import的问题。这篇文章会以flask里遇到的一个问题为原型，介绍一下
cicular import产生的原因，以及python中使用import文件时，到底python在做什么。

## 1. 一个cicular import实例

之前遇到一个cicular import的问题，项目文件结构大概如下：

```
flask_demo\
  app\
    auth\
      __init__.py
    __init__.py
  run_server.py
```

app目录下__init__.py文件内容如下：

```
from flask import Flask
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app

app = create_app()
login_manager = LoginManager(app)
```

app/auth目录下__init__.py文件内容如下：

```
from flask import Blueprint
from app import login_manager

# 注册蓝图
auth_bp = Blueprint('auth_bp', __name__)
```

最后运行run_server.py文件：

```
from app import app

app.run()
```

这个时候flask web应用并不会成功启动起来，而是会报下面的错误:

```
Traceback (most recent call last):
  File "/Users/caoxin/work/python_project/flask_demo/run_server.py", line 10, in <module>
    from app import app
  File "/Users/caoxin/work/python_project/flask_demo/app/__init__.py", line 24, in <module>
    app = create_app()
  File "/Users/caoxin/work/python_project/flask_demo/app/__init__.py", line 17, in create_app
    from app.auth import auth_bp
  File "/Users/caoxin/work/python_project/flask_demo/app/auth/__init__.py", line 11, in <module>
    from app import login_manager
ImportError: cannot import name 'login_manager' from 'app' (/Users/caoxin/work/python_project/flask_demo/app/__init__.py)
```

这是一个典型的cicular import问题，要解决这个问题，需要能够很好的理解，在python中使用import时，代码到底是如何运行的。


## 2. import执行过程

当我们import一个文件时，python会首先去查找这个文件之前是否被import过，如果这个文件之前有被import过，就不会重新再import一次。所以如果A模块
代码里import了B模块，并且B模块里又import了A模块，python的执行顺序会变成这样：

* 开始执行模块A
* 当A执行到import B的地方，则停止执行A模块后面的代码，转而开始执行B模块的代码
* 当B模块从头执行到import A的地方时，python此时**并不会**回过头去接着执行A剩余的代码，而且将A模块在**中断前已经初始化的属性**全加载到B模块中

我们以上面的例子来分件，app/__init__.py中create_app()方法中的from auth import auth_bp会中断app/__init__.py的执行，转而去执行
auth/__init__.py。需要注意的是，此时app/__init__.py里的app和login_manager两个属性都是声明的。而auth/__init__.py又想从app模块里导入
login_manager这个属性。很显然，这里就会报错。要解决这个问题，我们就需要重新设计代码结构，保证在auth/__init__.py在执行到from app import
login_manager时，app模块中已经定义了login_manager。如下：

```
from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager() # 在auth模块运行之前，先声明login_manager

def create_app():
    app = Flask(__name__)
    login_manager.init_app(app)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app

app = create_app()
```

所以理解了python在import时的工作原理，这种cicular import的问题便很好分析和解决了。