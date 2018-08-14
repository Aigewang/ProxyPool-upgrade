import time
from multiprocessing import Process
import asyncio
import aiohttp
try:
    from aiohttp.errors import ProxyConnectionError,ServerDisconnectedError,ClientResponseError,ClientConnectorError
except:
    from aiohttp import ClientProxyConnectionError as ProxyConnectionError,ServerDisconnectedError,ClientResponseError,ClientConnectorError
from proxypool.db import RedisClient
from proxypool.error import ResourceDepletionError
from proxypool.getter import FreeProxyGetter
from proxypool.setting import *
from asyncio import TimeoutError


class ValidityTester(object):
    test_api = TEST_API

    def __init__(self):
        self._raw_proxies = None
        self._usable_proxies = []

    def set_raw_proxies(self, proxies):
        self._raw_proxies = proxies
        self._conn = RedisClient()

    async def test_single_proxy(self, proxy):#定义协程函数
        """
        text one proxy, if valid, put them to usable_proxies.
        """
        try:
            async with aiohttp.ClientSession() as session:#aiohttp异步请求库，相当于s = requests.Session() ，创建一个session对象，然后用session对象去打开网页
                try:
                    if isinstance(proxy, bytes):#判断proxy是否是bytes类型
                        proxy = proxy.decode('utf-8')
                    real_proxy = 'http://' + proxy
                    print('Testing', proxy)
                    async with session.get(self.test_api, proxy=real_proxy, timeout=get_proxy_timeout) as response:#相当于response=urllib.request.urlopen(url)
                        if response.status == 200:
                            self._conn.put(proxy)
                            print('Valid proxy', proxy)
                except (ProxyConnectionError, TimeoutError, ValueError):
                    print('Invalid proxy', proxy)
        except (ServerDisconnectedError, ClientResponseError,ClientConnectorError) as s:
            print(s)
            pass

    def test(self):
        """
        aio test all proxies.
        """
        print('ValidityTester is working')

        loop = asyncio.get_event_loop()#启动协程函数
        tasks = [self.test_single_proxy(proxy) for proxy in self._raw_proxies]
        loop.run_until_complete(asyncio.wait(tasks))#tasks是一个asyncio.ensure_future(协程函数（参数））的列表，相当于多任务，异步执行tasks里的所有任务



class PoolAdder(object):
    """
    add proxy to pool
    """

    def __init__(self, threshold):#threshold是阀值
        self._threshold = threshold
        self._conn = RedisClient()
        self._tester = ValidityTester()
        self._crawler = FreeProxyGetter()#实例化元类

    def is_over_threshold(self):
        """
        judge if count is overflow.
        """
        if self._conn.queue_len >= self._threshold:#判断数据库内数据的数量是否溢出
            return True
        else:
            return False

    def add_to_queue(self):
        print('PoolAdder is working')
        proxy_count = 0
        while not self.is_over_threshold():#当数量没溢出时执行一下循环，创建类的实例对象
            for callback_label in range(self._crawler.__CrawlFuncCount__):#每个数字对应一个代理
                callback = self._crawler.__CrawlFunc__[callback_label]
                raw_proxies = self._crawler.get_raw_proxies(callback)#实例对象，此时raw_proxies具有__CrawlFuncCount__，__CrawlFunc__的属性
                # test crawled proxies
                self._tester.set_raw_proxies(raw_proxies)#传入抓取的免费代理
                self._tester.test()
                proxy_count += len(raw_proxies)
                if self.is_over_threshold():#溢出时进行的操作
                    print('IP is enough, waiting to be used')
                    break
            if proxy_count == 0:
                raise ResourceDepletionError


class Schedule(object):
    """从数据库取ip，进行检测"""
    @staticmethod
    def valid_proxy(cycle=VALID_CHECK_CYCLE):
        """
        Get half of proxies which in redis
        """
        conn = RedisClient()
        tester = ValidityTester()#创建实例
        while True:
            print('Refreshing ip')
            count = int(0.5 * conn.queue_len)
            if count == 0:
                print('Waiting for adding')
                time.sleep(cycle)
                continue
            raw_proxies = conn.get(count)#调用conn = RedisClient()中get方法，get方法是获取代理
            tester.set_raw_proxies(raw_proxies)
            tester.test()
            time.sleep(cycle)

    @staticmethod
    def check_pool(lower_threshold=POOL_LOWER_THRESHOLD,
                   upper_threshold=POOL_UPPER_THRESHOLD,
                   cycle=POOL_LEN_CHECK_CYCLE):
        """
        If the number of proxies less than lower_threshold, add proxy
        """
        conn = RedisClient()
        adder = PoolAdder(upper_threshold)#创建类实例时传入阀值上限
        while True:
            if conn.queue_len < lower_threshold:
                adder.add_to_queue()
            time.sleep(cycle)

    def run(self):
        print('Ip processing running')
        valid_process = Process(target=Schedule.valid_proxy)#申请子进程，循环从数据库拿出代理，进行检测
        check_process = Process(target=Schedule.check_pool)#从网上获取代理，进行筛选，将代理放入数据库
        valid_process.start()#开始子进程
        check_process.start()
        valid_process.join()
        check_process.join()
