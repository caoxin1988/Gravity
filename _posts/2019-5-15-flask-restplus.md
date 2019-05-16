---
layout: post
title:  "falsk插件flask-restplus"
author: dacaoxin
date:   2019-5-15 23:25:00
categories: [python, flask]
---

在编写web应用程序时，需要实现RESTful的api功能非常常见，当然我们可以使用flask来编写路由，实现RESTful api，但是Flask提供了便捷的方法，就是
Flask-RESTful和FLASK-RESTplus。但是相对于Flask-RESTFul, Flask-RESTplus不但可以方便的实现restful api, 同时它还集成了Swagger的文档
化功能，所有的api都会在swagger页面上展示，同时在swagger页面上也提供了对api的测试方法。

## 1. 安装并初始化

使用下面的命令安装flask-socketio：

> $ pip install flask-restplus

接下来可以初始化flask-restplus插件:

```
from flask import Flask
from flask_restplus import Api

api = Api()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config')
    api.init_app(app)
    return app

app = create_app()
```

## 2. 使用flask-restplus

接下来可以使用api对象设置一个最简单的路由:

```
@api.route('/hello')
class Hello(Resource):
    def get(self):
        return {'hello': 'world'}
```

Hello类继承于Resource类，其成员函数的名字和增(post)，删(delete)，改(put)，查(get)等http方法的名字需要一样，这样在请求到来时，flask会根
据请求方法的名字来找到对应的同名的函数调用, 如果找不到，就会抛出方法未实现的异常。

启动web服务器程序，访问http://localhost:5000/hello，会得到返回的结果：

```
{
    "hello": "world"
}
```

*@api.route()*装饰器也支持为资源添加多个url，这样通过这些url的访问，都会被路由到同一个资源里。比如

```
@api.route('/hello', '/world')
```

### 2.1 请求参数处理

同本身的Flask一样，flask-restplus也支持将url中的部分内容设成变量:

```
@api.route('/index/<string:id>')
class Index(Resource):
    def get(self, id):
        return {'id': '{}'.format(id)
```

虽然Flask提供了request.form来接收post请求的参数，但是验证表单数据仍然非常头疼，需要借助使用flask-wtform插件完成。而flask-restplus内置
了对请求数据的验证功能，通过reqparse实现:

```
parser = reqparse.RequestParser()
parser.add_argument('data', type=int, required=True, help='data should be int')
parser.add_argument('id', type=int, required=True, help='id should be int')

@api.route('/index')
class Index(Resource):
    def get(self):
        return {'id': '{}'.format(id)}

    def post(self):
        args = parser.parse_args()
        data, id = args['data'], args['id']
        return {'data': data, 'id': id}
```

当data和id两个参数传递的值不满足上面要求时，验证不通过，同时会在网页端显示help里定义的信息。

### 2.2 返回数据格式化

上面的例子里，所有请求方法定义的函数返回值都是python内置的数据结构，它些对象可以直接被序列化后原样返回。但是如果我们需要返回一个自定义的类对象
的时候，就需要使用*@api.marshal_with*装饰器做特殊处理，否则会报错, 看个例子:

```
model = api.model('Model', {
    'id': fields.String,
    'task': fields.String
})

class Dao():
    def __init__(self, id, task):
        self.id = id
        self.task = task
        self.status = 'done' # 这个定不会返回，使用了marshal_with, 就只api.model里写明的数据

@api.route('/todo')
class Todo(Resource):
    @api.marshal_with(model)
    def get(self):
        return Dao(id='1', task='drink milk')
```

当访问http://localhost:5000/todo时，会返回

```
{
    "id": "1",
    "task": "drink milk"
}
```

如果没有使用*@api.marshal_with()*这个装饰器，这次请求就会报错。也可以使用marshal()方法来替代*@api.marshal_with()*装饰器：

```
@api.route('/todo')
class Todo(Resource):
    def get(self):
        return marshal(Dao(id='1', task='drink milk'), model)
```

有时候，我们需要返回的字段名可能和真实的字段名不一样，这个时候可以通过attribute传递真实的字段名实现。

```
model = api.model('Model', {
     'idx': fields.String(attribute='id'), # 使用attribute做了一次字段名字映射
     'task': fields.String
})
``·

### 2.3 内置Swagger

Swagger是一个规范和完整的框架，用于生成、描述、调用和可视化RESTful风格的 Web 服务。主要是为了方便RESTful api的接口文档在线生成，并且方便
直接在网页端对restful api进行在线测试。flask-restplus里集成了swagger的功能。直接访问服务器的root url就会打开swagger的前端页面。显示
效果如下：

![swagger](/images/restplus/swagger.png)

可以为整个类或者某一个方法添加@api.doc()装饰器使api在swagger页面里可以具体的显示每个参数的类型以及返回码信息。默认的在swagger里只有200这一个
返回码。

```
@api.route('/hello')
@api.doc(params={'id': 'An ID'})
class Hello(Resource):
    def get(self):
        return {'hello': 'world'}

    @api.doc(responses={403: 'Not Authorized'})
    def post(self, id):
        api.abort(403)
```

同时，上一节中，使用*@api.marshal_with()*标明的返回数据格式，也会在Swagger页面展示出来。


想要获取完整代码，请点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/restplus)