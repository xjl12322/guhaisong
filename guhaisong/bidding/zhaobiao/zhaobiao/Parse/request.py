# coding=utf-8
import requests
from fake_useragent import UserAgent


def get(url, proxy=None, header=None, retry=0, type=None):
    #header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
    header = {'User-Agent': UserAgent().random} if header is None else header
    try:
        response = requests.get(url, headers=header, proxies=proxy, timeout=10)
        if response.status_code in [i for i in range(200, 300)]:
            if type is not None:
                response.encoding = type
            return response.text
        else:
            retry += 1
            return get(url, proxy, header, retry) if retry <= 10 else None
    except Exception as e:
        print('请求错误:{}'.format(e))
        retry += 1
        return get(url, proxy, header, retry) if retry <= 10 else None


def post(url, data, proxy=None, header=None, retry=0, type=None):
    header = {'User-Agent': UserAgent().random} if header is None else header
    #header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
    try:
        response = requests.post(url, headers=header, proxies=proxy, data=data, timeout=10)
        if response.status_code in [i for i in range(200, 300)]:
            if type is not None:
                response.encoding = type
            return response.text
        else:
            retry += 1
            return post(url, data, proxy, header, retry) if retry <= 10 else None
    except Exception as e:
        print('请求错误:{}'.format(e))
        retry += 1
        return get(url, data, proxy, header, retry) if retry <= 10 else None


if __name__ == '__main__':
    url = 'http://www.hebpr.cn/hbjyzx/002/002009/002009001/002009001002/1c26a44d-04b7-4a6e-9b5a-26aee05fa6fc.html'
    print(get(url))
