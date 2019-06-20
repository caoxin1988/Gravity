---
layout: post
title:  "docker-compose使用"
author: dacaoxin
date:   2019-6-20 18:35:00
categories: [docker, docker-compose]
---

> 更多精彩内容，欢迎关注微信公众号: tmac_lover

## 什么是docker compose
* Docker compose是一个配置多个docker容器启动的工具
* 通过yml文件定义多容器的docker应用
* 只需要一条命令就可以根据yml文件的定义来创建或管理多个容器(如启动，停止，删除等)

## docker compose组成
Docker-compose.yml文件有三个大组部分：services, networks, volumes
一个 service代表一个container, 这个container可以由dockerhub上的image来创建，也可以从本地的dockerfile build出来的image创建

## docker-compose示例
一个很简单的docker-compose.yml示例如下：

```docker
version: '3'
services:
  web:
    build: .
	  ports:
      - "5000:5000"
  redis:
    image: "redis:latest"
```

可以使用命令：

```shell
> $ docker-compose -p test -f docker-compose.yml up [-d]
```

来通过docker-compose.yml启动配置文件中的容器，更多关于`docker-compose`命令的使用，可以使用以下命令查看:

```shell
> $ docker-compose
```

1. network隔离

使用上面命令时，docker-compose会默认创建一个名为`test_default`的network bridge, 使得.yml里的所有container都连接上去，这样所有的容器之间，就可以使用service name相互访问了。比如上面的web容器可以直接使用`redis://redis:6379/0`来访问redis数据库。

不过docker compose也可以使不同的容器之间网络相互隔离，在docker-compose.yml里如下配置:

```docker
version: '3'
services:
  proxy:
    image: nginx
    ports:
      - "80:80"
    networks:
      - frantnet
  webapp:
    build: .
    networks:
      - frantnet
      - endnet
  redis:
    image: redis
    networks:
      - endnet
networks:
  frantnet:
  endnet:
```

这个.yml配置文件会启动三个容器，并创建两个虚拟网络：frantnet和endnet。配置中的写法，会让proxy容器和webapp容器网络相连，而webapp和redis相连

2. 定义容器启动顺序

一般来说，.yml文件里定义的容器启动顺序是随机的，不过也可以像下面这样使用`depends_on`定义启动顺序依赖。

```docker
version: '3'
services:
  web:
    build: .
	  ports:
      - "5000:5000"
	  depends_on:
		- redis
  redis:
    image: "redis:latest"
```

3. 配置volume

Docker提供volume使容器中的数据持久化。在.yml文件中有两种方式来定义volume:

* 命名的volume
* 指定到主机上的路径

```docker
version: '3'
services:
  web:
    image: nginx:alpine
    volumes:
      - type: volume
        source: mydata
        target: /data
      - type: bind
        source: ./nginx/logs
        target: /var/log/nginx
  redis:
    image: redis
    volumes:
      - jenkins_home:/var/jenkins_home
      - mydata:/data
volumes:
  mydata:
  jenkins_home:
```

web容器和redis容器通过命名的volume名字mydata来共享，而web容器也将`/var/log/nginx`目录映身到本地的`./nginx/logs`目录下。

4. 水平扩展与负载均衡

使用命令

```shell
> $ docker-compose -f docker-compose.yml up -d --scale web=3
```

需要注意的是，如果使用水平扩展，则在.yml里不能使用`ports`将端口映射到本地宿主机上，否则会在扩展时报端口被重复监听的错误。