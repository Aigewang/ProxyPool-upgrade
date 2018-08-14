from flask import Flask, g

from .db import RedisClient

__all__ = ['app']#暴露app接口，其中all是对于模块接口的一种约定

app = Flask(__name__)#得到Flask 类的实例对象 app


def get_conn():
    """
    Opens a new redis connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'redis_client'):#hasattr(object, name)判断一个对象里面是否有name属性或者name方法，返回BOOL值，有name特性返回True， 否则返回False。
        g.redis_client = RedisClient()
    return g.redis_client

# 使用路由 为URL 绑定视图函数
@app.route('/')#这个函数级别的注解指明了当地址是根路径时，就调用下面的函数。表示传递一个网站，“/”是网站的主目录，也就是http://127.0.0.1:5000/
def index():
    return '<h2>Welcome to Proxy Pool System</h2>'


@app.route('/get')
def get_proxy():
    """
    Get a proxy
    """
    conn = get_conn()
    return conn.pop()


@app.route('/count')
def get_counts():
    """
    Get the count of proxies
    """
    conn = get_conn()
    return str(conn.queue_len)


if __name__ == '__main__':
    app.run()
