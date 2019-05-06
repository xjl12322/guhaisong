# coding=utf-8
import requests
from fake_useragent import UserAgent


# 私有请求模块
def _request(url, times=0, type='text'):
    Retry_times = 5  # 重试次数
    try:
        res = requests.get(url, headers={
            'User-Agent': UserAgent().random
        }, timeout=3)
        if type == 'text':
            return res.text
        if type == 'byte':
            return res.content
    except:
        times += 1
        return _request(url, times) if times <= Retry_times else None


if __name__ == '__main__':
    pass
