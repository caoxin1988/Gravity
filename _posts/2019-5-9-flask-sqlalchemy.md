---
layout: post
title:  "falsk插件flask-sqlalchemy"
author: dacaoxin
date:   2019-5-9 20:14:00
categories: [python, flask]
---

使用flask编写web应用程序时，不可避免的会要使用数据据，特别是关系型数据库mysql。为了简化对数据库的操作，出现在对象关系映射ORM框架。
Flask-SQLAlchemy是基于SQLAlchemy实现的一个插件。

## 1. 安装

使用命令:

> $ pip install flask-sqlalchemy

安装。之后可以初始化flask-sqlalchemy

```
app = Flask(__name__)
app.config.from_object('app.config')

db = SQLAlchemy()
db.init_app(app)
db.create_all(app=app)
```

使用flask-sqlalchemy必须要在config里配置SQLALCHEMY_DATABASE_URI。

```
SQLALCHEMY_DATABASE_URI = 'sqlite:///db/users.db'
```

这里我们使用SQLite3数据库。所以使用'sqlite:///'开头，之后可以使用绝对路径，也可以使用相对路径。绝对路径需要以'/'开头。这里使用的是相对路径，
表示当前目录下db/users.db这个数据库。然后运行程序，可以看到在db目录下有了users.db这个数据库。但是数据库文件里没有任何数据表。


## 2. 创建数据表模型

通过定义一个继承db.Model的类，便定义了一个模型，这个模型便对应数据库中的一个表。

```
class User(db.Model):
    id = db.Column(db.Integer,  primary_key=True)
    name = db.Column(db.String(50), unique=True)
    age = db.Column(db.Integer)

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return '<User %r>' % self.name
```

之后再运行程序，db.create_all()会同时在数据库users.db里创建一个表user。上面的模型类似于执行下列sql语句。

```
CREATE TABLE user (
        id INTEGER NOT NULL,
        name VARCHAR(50),
        age INTEGER,
        PRIMARY KEY (id),
        UNIQUE (name)
);
```

同时，可以使用db.drop_all()这行代码实现删除所有数据表，但是数据库文件users.db会被保留。需要注意的是，必须在db.create_all()调用之前导入
数据表模型才会在数据库中创建数据表。

## 3. 增删改查

### 3.1 添加数据

使用下面代码可以往数据库中添加数据:

```
@app.route('/add')
def add():
    db.session.add(User('tom', 18))
    db.session.add(User('cat', 20))
    db.session.commit()

    return 'add successfully'
```

记得要调用db.session.commit()提交事务，不然数据不会放到数据库中。

### 3.2 查找数据

每个数据模型可以通过query接口从相应表中查询数据，查询user表中所有数据:

```
user = User.query.all()
```

也可以使用filter_by()方法对查询结果进行过滤：

```
user = User.query.filter_by(name='tom').all()
```

还可以filter()方法以范围对结果进行过滤:

```
user = User.query.filter(User.age>17).all()
```

所有的查询结果通过all()全部获取，也可以通过first()只获取第一个。


### 3.3 更新数据

更新数据可以使用add()更新数据：

```
user = User.query.filter_by(name='Tom').first()
if user:
    user.age += 1
    db.session.add(user)
    db.session.commit()
```

也可以使用update()方法实现更新：

```
User.query.filter_by(name='tom').update({'age': User.age+1})
db.session.commit()
```

同样，更新之后需要使用commit()提交事务。


### 3.4 删除数据

删除方法和添加方法有些类似，使用delete()方法可以实现：

```
user = User.query.filter_by(name='tom').first()
if user:
    db.session.delete(user)
    db.session.commit()
```

## 4. 一对多模型

在使用MySQL这种关系型数据库时，经常会用到多表连接的情况，SQLAlchemy也提供了这种一对多的模型。

```
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course = db.Column(db.String(50))
    access_date = db.Column(db.DateTime)
    score = db.Column(db.Float)
    name = db.Column(db.String(50))
    is_access = db.Column(db.Boolean)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('scores', lazy='dynamic'))

    def __init__(self, course, score, user, assess_date=None):
        self.course = course
        self.score = score
        self.is_pass = (score >= 60)
        if assess_date is None:
            assess_date = datetime.now()
        self.name = user.name
        self.assess_date = assess_date
        # self.user = user

    def __repr__(self):
        return '<Course %r of User %r>' % (self.course, self.user.name)
```

Score模型定义的属性中，'user_id'是申明的一个外键，表明了score表和user表之间关联关生活费，'user'并不是数据表中的一个字段，它使用
'db.relationship()'方法可以让我们在代码中使用‘Score.user’访问当前score记录的一个对象, 它的第一个参数'User'就表明这个属性使用的对象模
型是'User'。第二个参数'backref‘定义了从User模型反向引用Score模型的方法，我们可以使用'User.scores'获取当前user对象所有的记录。

### 4.1 添加记录

可以使用如下代码添加记录:

```
@app.route('/score_add')
def score_add():

    user = User.query.filter_by(name='tom').first()
    if user:
       db.session.add(Score('Math', 80.5, user))
       db.session.add(Score('Art', 95, user))
       db.session.commit()

    return 'score add successfully'
```

可以使用'User.scores'查询某个用户的成绩:

```
@app.route('/score_find')
def score_find():
    name = request.args.get('name')

    user = User.query.filter_by(name=name).first()
    if user:
        for score in user.scores:
            print('name {}, course: {}, score: {};'.format(score.name, score.course, score.score))

    return 'score find successfully'
```

获取示例代码，请点击[这里](https://github.com/caoxin1988/flask_demo/tree/master/sqlalchemy)
