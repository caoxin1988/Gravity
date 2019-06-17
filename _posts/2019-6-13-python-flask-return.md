---
layout: post
title:  "flask视图函数返回形式"
author: dacaoxin
date:   2019-6-13 11:59:00
categories: [python, flask]
---

使用flask编写web应用程序时很重要的一个工作就是路由的视图函数编写。对于刚接触flask的人来说，有时候会觉得很奇怪，为什么路由的视图函数返回值
有好几种写法，今天总结一下视图函数返回值的种类，并简要分析一下，这几种返回值的本质，以及它们最终是如何返回给流览器的。

## flask视图函数返回值的几种形式

先列出常见的几种flask视图函数返回值的形式：

* 返回一个字符串

```python
@app.route('/test')
def test():
    return 'hello world!'
```

* 返回render_template
```python
@app.route('/test')
def test():
    return render_template('index.html')
```

* 返回jsonify
```python
@app.route('/test')
def test():
    return jsonify({'name': 'tom'})
```

* 返回元组
```python
@app.route('/test')
def test():
    # 返回元组时，顺序依次是：返回内容，返回状态码，返回的header
    return 'hello world', 200, {'Locateion':'www.baidu.com'}

    # 也可以使用jsonify返回元组
    # return jsonify({}), 200, {'Locateion':'www.baidu.com'}
```

* 返回make_response
```python
@app.route('/test')
def test():
    response = make_response('hello')
    response.headers = {'Location':'abc'}
    return response
```

基本上常见的就是以上几种形式，看上去是不是有些眼花缭乱？其实在了解了flask里视图函数的返回值是如何被组装处理的，那就不会感到凌乱，并且会有助于记忆。

## 标准WSGI接口

实际上，flask是基于Werkzeug工具包的一个web服务框架，所以flask里视图函数的实现，实际上是对werkzeug的一层封装，我们先看一下一个简单的
werkzeug应用是怎么实现的：

```python
from werkzeug.wrappers import Request, Response

def application(environ, start_response):
    request = Request(environ)
    text = 'Hello %s!' % request.args.get('name', 'World')
    response = Response(text, mimetype='text/plain')
    return response(environ, start_response)
```

可以看到，实际上werkzeug要求每次请求的返回值是Response类型。所以实际上，flask的视图函数返回值无论如何变，它都不会离开Response类型。


## flask里组装过程

flask视图函数调用过程如下：

```plain
rv = full_dispatch_request() [class Flask]
     -> dispatch_request()   [class Flask]
        -> self.view_functions[rule.endpoint](**req.view_args)
finalize_request(rv)
    -> make_response(rv)    [class Flask]
        -> rv = self.response_class(rv, status=status, headers=headers) [class Flask]
            # 这里response_class实际上就是Response类
           return rv  
```

可以看到，无论flask里视图函数的返回值是什么样式，最终都会调用Flask.make_response()里的response_class构造一个Response对象。回头看flask
视图函数的返回值：
* 如果返回的是3个元素的元组，则会在构造Response时使用元组里的后两个作为Response的返回code以及header
* 如果返回的值是单个元素
  * 如果是字符串，那么在Flask.make_response()里会加上默认的code和header，并且header里content-type是text/html
  * 如果是jsonify(), 会在jsonify()方法里组装一个Response对象，并在header里添加content-type为text/json。然后返回
* 如果返回的是render_template, 会通过flask里的渲染引擎将html渲染成字符串返回，之后便和返回字符串形式相同
* 如果返因的是make_response, 则会直接生成Response对象

在Flask.make_response()里，会根据视图函数返回的值的个数，类型的不同，来做不同的处理，生成最终的Response对象，并为字添加code和header等。

无论如何，看源码，是最有效的学习方法。
