---
layout: post
title:  "falsk插件flask-restful"
author: dacaoxin
date:   2019-5-12 13:14:00
categories: [python, flask]
---

在编写web应用程序时，需要实现RESTful的api功能非常常见，当然我们可以使用flask来编写路由，实现RESTful api，但是Flask提供了便捷的方法，即
使用Flask-RESTful扩展。

## 1. 安装

可以使用下面的命令安装flask-restful插件：

> $ pip install flask-restful

安装之后，可以这样初始化使用。

```
api = Api()
app = Flask(__name__)
app.config.from_object('app.config')

from app import views   # 加载Resource，使用api.init_app()这种方式，必须要先加载Resource才行，否则路由注册不成功

api.init_app(app)
```

## 2. 注册RESTful api

views.py的代码如下：

```
from app import api

USER_LIST = {
    '1': {'name': 'cat'},
    '2': {'name': 'tom'}
}

class UserList(Resource):
    def get(self):
        return USER_LIST

    def post(self):
        user_id = int(max(USER_LIST.keys())) + 1
        user_id = '%i' % user_id
        USER_LIST[user_id] = {'name': request.form['name']}

        return USER_LIST

api.add_resource(UserList, '/users')
```

UserList类继承于Resource类，其成员函数的名字和增(post)，删(delete)，改(put)，查(get)等http方法的名字需要一样，这样在请求到来时，
flask会根据请求方法的名字来找到对应的同名的函数调用, 如果找不到，就会抛出方法未实现的异常。

以上代码实现在http://127.0.0.1:users的GET和POST请求。

这里需要注意的是，如果使用api.init_app()的方法来初始化flask-restful对象，需要保证api.add_resource()必须在apo.init_app()之前调用，否
则无法注册成功路由。

另外，flask_restful也支持多路由注册:

```
apo.add_resource(UserList, '/users', '/userlist')
```

## 3. 带参数请求

flask-restful和flask一样，可以在url中添加参数:

```
class User(Resource):
    def get(self, user_id):
        return USER_LIST[user_id]

    def delete(self, user_id):
        USER_LIST.pop(user_id)
        return USER_LIST

    def put(self, user_id):
        USER_LIST[user_id] = {'name': request.form['name']}
        return USER_LIST

api.add_resource(User, '/user/<user_id>')
```

上面代码中，put中通过request.form来获取参数，flask_restful中提供了更简单的方法来实现这个功能：

```
from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('name', type=str)

class User(Resource): 
    def put(self, user_id):
        args = parser.parse_args()
        USER_LIST[user_id] = {'name': args['name']}
        return USER_LIST
```

想要获取完整代码，请点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/restful)