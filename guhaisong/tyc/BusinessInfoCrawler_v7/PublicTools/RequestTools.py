# coding=utf-8
import requests
from PublicTools.UserAgentTools import UserAgentHelper


class RequestHelper:
    def __init__(self):
        self.url = None
        self.data = None
        self.proxies = None
        self.cookies = None
        self.status_code = None
        self.response_headers = None
        self.UserAgent = UserAgentHelper.UserAgent()
        self.session = requests.session()

    def get(self, url, headers=None, proxy=None,
            cookies=None, timeout=None, decode=None, times=3, mode=True):
        # 必要参数url,可选参数headers,proxy,其中proxy的格式为:0.0.0.0:0000
        # timeout 为延迟时间，默认为5s，times为错误或异常重试次数默认为3
        default_headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'Keep-Alive',
            'Referer': 'https://www.baidu.com/',
            'User-Agent': self.UserAgent.UA()
        }
        headers = default_headers if headers is None else headers
        timeout = 5 if timeout is None else timeout
        decode = 'utf-8' if decode is None else decode
        proxies = None if proxy is None else {
            'http': 'http://{}'.format(proxy),
            'https': 'https://{}'.format(proxy),
            'ftp': 'ftp://{}'.format(proxy),
        }
        self.url = url
        self.proxies = proxies
        request = requests if mode else self.session
        try:
            response = request.get(
                url,
                headers=headers,
                proxies=proxies,
                cookies=cookies,
                timeout=timeout,
                verify=True,
            )
            response.encoding = decode
            self.cookies = response.cookies.items()
            self.status_code = response.status_code
            self.response_headers = response.headers
            return response.text
        except Exception as e:
            print(e)
            return None if times <= 0 else self.get(
                url, headers, proxy, cookies, timeout, decode, times - 1, mode)

    def post(self, url, data=None, headers=None, proxy=None,
             cookies=None, timeout=None, decode=None, times=3, mode=True):
        # 必要参数url,可选参数headers,proxy,其中proxy的格式为:0.0.0.0:0000
        # data为post的数据且已被格式化
        # timeout 为延迟时间，默认为5s，times为错误或异常重试次数默认为3
        default_headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'Keep-Alive',
            'Referer': 'https://www.baidu.com/',
            'User-Agent': self.UserAgent.UA()
        }
        headers = default_headers if headers is None else headers
        timeout = 5 if timeout is None else timeout
        decode = 'utf-8' if decode is None else decode
        proxies = None if proxy is None else {
            'http': 'http://{}'.format(proxy),
            'https': 'https://{}'.format(proxy),
            'ftp': 'ftp://{}'.format(proxy),
        }
        self.url = url
        self.proxies = proxies
        request = requests if mode else self.session
        try:
            response = request.post(
                url,
                data=data,
                headers=headers,
                proxies=proxies,
                timeout=timeout,
                verify=True
            )
            response.encoding = decode
            self.cookies = response.cookies
            self.status_code = response.status_code
            self.response_headers = response.headers
            return response.text
        except Exception as e:
            print(e)
            return None if times <= 0 else self.post(
                url, data, headers, proxy, cookies, timeout, decode, times - 1, mode)

if __name__ == '__main__':
    RequestHelper = RequestHelper()
    print(RequestHelper.UserAgent.UA())
    
