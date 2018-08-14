import requests
import asyncio
import aiohttp
from requests.exceptions import ConnectionError
from fake_useragent import UserAgent,FakeUserAgentError
import random

def get_page(url, options={}):
    try:
        ua = UserAgent()
    except FakeUserAgentError:
        pass
    base_headers = {
        'User-Agent':  ua.random,
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8'
    }
    headers = dict(base_headers, **options)
    print('Getting', url)
    try:
        r = requests.get(url, headers=headers)
        print('Getting result', url, r.status_code)
        if r.status_code == 200:
            return r.text
    except ConnectionError:
        print('Crawling Failed', url)
        return None


class Downloader(object):
    """
    一个异步下载器，可以对代理源异步抓取，但是容易被BAN。
    async def 用来定义异步函数，其内部有异步操作。
    每个线程有一个事件循环，主线程调用asyncio.get_event_loop()时会创建事件循环，
    你需要把异步的任务丢给这个循环的run_until_complete()方法，事件循环会安排协同程序的执行。
    """

    def __init__(self, urls):
        self.urls = urls
        self._htmls = []

    async def download_single_page(self, url):        #定义协程函数
        async with aiohttp.ClientSession() as session:  #建立session
            async with session.get(url) as resp:       #session发送get请求，返回值给resp
                self._htmls.append(await resp.text())    #await 关键字加在需要等待的操作前面

    def download(self):
        loop = asyncio.get_event_loop()
        tasks = [self.download_single_page(url) for url in self.urls]
        loop.run_until_complete(asyncio.wait(tasks))

    @property
    def htmls(self):
        self.download()
        return self._htmls
