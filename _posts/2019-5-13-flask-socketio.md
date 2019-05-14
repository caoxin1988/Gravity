---
layout: post
title:  "falsk插件flask-socketio"
author: dacaoxin
date:   2019-5-13 20:01:00
categories: [python, flask]
---

flask-socketio模块实际上是封装了flask对websocket的支持，更方便我们进行websocket编程。websocket和http一样是一种基于tcp/ip的应用层
通信协议，它们完全是并列的两种协议。但是websocket在建立连接时，需要通过http的握手方式进行，当连接一旦建立成功，便不再需要Http通信了，所有的交
互都由websocket协议直接接管。Flask-SocketIO使Flask应用程序可以访问客户端和服务器之间的低延迟双向通信，使客户端建立与服务器的永久连接.

flask-socketio适合那种后台产生新数据，马上要推送给前端的场景，例如数据监控，统计图实时变化，后台推送消息等场景。

## 1. 安装

使用下面的命令安装flask-socketio：

> $ pip install flask-socketio

flask_socketio异步服务需要依赖第三方异步模块的支持。flask_socketio支持的异步模块有: eventlet和gevent。可以使用下面命令安装:

> $ pip install eventlet
> $ pip install gevent gevent-websocket

代码中初始化SocketIO()时，可以通过*async_model*参数指定使用的异步模块，如果不指定，flask_socketio会按照尝试eventlet，如果未安装eventlet
再尝试gevnet。eventlet可以提供长轮循和websocket两种方式; 而gevent只支持长轮循，如果要支持websocket,需要同时安装gevent-websocket，或
者使用uWSGI服务器。

如果eventlet和gevnet都没有安装，就会使用flask自带的基于Werkzeug的开发服务器, 但是它只支持长轮循方式。这种方式性能很差，只适合调试使用。

对客户端来说，javascript, swift, java, c++都有官方支持的Socket.IO库; 不过也可以使用非官方的库，只要它支持socket.io协议即可。

## 2. 使用flask-socketio

使用以下代码可以完成flask-socketio的初始化:

```
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config')
    return app

app = create_app()
socketio.init_app(app)
```

然后可以在服务端可以实现事件回调和消息发送方法：

```
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('my event', namespace='/test_conn')
def test_connect(message):
    print(message['data'])
```

在flask-socketio中，消息在客户端和服务端是通过事件的方式传递的，上面的*namespace=*就相当于定义了一个websocket连接，装饰器@socketio.on()
的第一个参数相当于是正在监听的一个事件,一个连接上可以有多个不同的事件。当服务端收到test_conn连接里的'my event'事件之后，就会回调test_connect()
这个方法。

再看看客户端javascript的实现:

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title></title>
    <script type="text/javascript" src="https://cdn.bootcss.com/jquery/3.4.1/jquery.min.js"></script>
    <script type="text/javascript" src="https://cdn.bootcss.com/socket.io/1.5.1/socket.io.min.js"></script>
</head>
<body>
<h1>ready to start test!</h1>
<h2 id="t"></h2>
<script type="text/javascript">
$(document).ready(function() {
	        namespace = '/test_conn';
	        console.log('document ready')
            var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
	        socket.on('connect', function(msg) {
	            socket.emit('my event', {data: "i'm connected"})
            })
            socket.on('event response', function (msg) {
                console.log(msg['data'])
                console.log('in event response')
            })
            socket.on('mess', function (msg) {
                console.log(msg['data'])
                $('#t').text(msg['data'])
            })
	});
</script>
</body>
</html>
```

客户端和服务端一样，使用socket.emit()方法发送消息，客户端通过connect()指定连接到哪个websocket链接上。通过socket.on()表示监听哪个事件。

当然使用flask-socketio可以让服务端主动向客户端推送消息:

```
thread = None

def background_task():
    while True:
        socketio.sleep(5)
        t = random.randint(1, 100)
        socketio.emit('mess', {'data': t}, namespace='/test_conn')

@socketio.on('connect', namespace='/test_conn')
def test_connect():
    global thread

    if thread is None:
        thread = socketio.start_background_task(target=background_task)
```
这里让服务端循环向客户端推送消息时，如果直接在test_connect()里进行循环的话，最后会发现它客户端并不会有收到消息，比如下面这样:

```
@socketio.on('connect', namespace='/test_conn')
def test_connect():
    while True:
        socketio.sleep(5)
        print('background task emit')
        t = random.randint(1, 100)
        socketio.emit('mess', {'data': t}, namespace='/test_conn')
```

写得更简便一点，如果test_connect()里连写两条socket.emit()，客户端会有返回，但是并不是收到一条消息就返回一次，而是两条消息都发送完成之后，才会
收到返回。这里原因还不是特别清楚，但是需要注意这里的坑。还有就是，使用一个background_task来实现时，target函数里一定要使用socketio.emit(),
而不能直接写emit()，否则会报RuntimeError: Working outside of request context的错误。这里应该是因为socketio里带有请求上下文信息。

另外一个flask-socketio里很有一个非常有用的功能，就是向所有连接在某个namespace上的客户端同时广播消息。通过在emit()里加上*broadcast=True*参数:

```
@socketio.on('my event broadcast', namespace='/test_conn')
def test_connect(message):
    emit('my ev broadcast', message, broadcast=True)
```

有一点需要注意，上面通过background_task来向客户端发送消息时，直接使用socketio.emit()方法，这里的socketio并没有任何客户端请求信息，所以这
时emit()默认直接加上了*broadcast=True*选项了。


想要获取完整代码，请点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/socketio)