import redis
from proxypool.error import PoolEmptyError
from proxypool.setting import HOST, PORT, PASSWORD


class RedisClient(object):
    def __init__(self, host=HOST, port=PORT):
        if PASSWORD:
            self._db = redis.Redis(host=host, port=port, password=PASSWORD)#与数据库链接
        else:
            self._db = redis.Redis(host=host, port=port)

    def get(self, count=1):
        """
        get proxies from redis
        """
        proxies = self._db.lrange("proxies", 0, count - 1)#lrang从队列的左侧拿出多少数据，然后返回，从左侧批量获取
        self._db.ltrim("proxies", count, -1)
        return proxies

    def put(self, proxy):
        """
        add proxy to right top
        """
        self._db.rpush("proxies", proxy)

    def pop(self):
        """
        get proxy from right.
        """
        try:
            return self._db.rpop("proxies").decode('utf-8')
        except:
            raise PoolEmptyError
    """设置属性进行计算数据库的数据值以及更新数据库"""

    @property
    def queue_len(self):
        """
        get length from queue.
        """
        return self._db.llen("proxies")#计算数据库中proxies的数量

    def flush(self):
        """
        flush db
        """
        self._db.flushall()#刷新数据库


if __name__ == '__main__':
    conn = RedisClient()
    print(conn.pop())
