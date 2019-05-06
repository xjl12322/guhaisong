# coding=utf-8
import requests
import time
import json
import config
from copy import deepcopy
from PublicTools.RequestTools import RequestHelper
from PublicTools.UserAgentTools.UserAgentHelper import UserAgent

class CodeApi:
    def __init__(self):
        self.UserAgent = UserAgent()
        self.headers = {
            'Host': 'ss.cods.org.cn',
            'Connection': 'close',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': UserAgent().UA(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.ProxyTunnel = 1
        self.RequestHelper = RequestHelper()

    # 第一次探测式请求,必须使用同一个代理ip
    def probe(self, headers):
        url = 'https://ss.cods.org.cn/usercenter/regLogin'
        # self.RequestHelper.get(url, headers=headers)
        
        # self.RequestHelper.get(url, headers=headers, proxy='114.234.80.241:23987')
        self.RequestHelper.get(url, headers=headers, proxy=self.proxies)
        [cookies] = self.RequestHelper.cookies
        # a = self.RequestHelper.get(url='http://httpbin.org/ip', headers=headers)
        a = self.RequestHelper.get(url='http://httpbin.org/ip', headers=headers,proxy=self.proxies)
        print('探测', a)
        try:
            return cookies[1]
        except Exception as e:
            return print(e)

    # 获取极验参数
    def get_jiyan_param(self, headers):
        url = 'https://ss.cods.org.cn/gc/geetest/login?t={}'.format(int(time.time() * 1000))
        response = self.RequestHelper.get(
            url=url,
            # proxy=config.proxyMeta,
            # proxy='114.234.80.241:23987',
            proxy=self.proxies,
            headers=headers,
            timeout=10
        )
        a = self.RequestHelper.get(url='http://httpbin.org/ip', headers=headers,proxy=self.proxies)
        print('获取及验参数', a)
        try:
            res_json = json.loads(response)
            res_dict = eval(res_json.replace('true', '1'))
            if res_dict['success'] != 1:  # 返回状态是1表示正常
                return
            return (res_dict['gt'], res_dict['challenge'])
        except:
            return

    # 极验证参数破解
    def jiyan_crack(self, gt, challenge):
        api = 'http://jiyanapi.c2567.com/shibie?gt={}&challenge={}&referer=' \
              'https://ss.cods.org.cn&user=cbi&pass=abcd-1234&return=json&model=3&format=utf8'
        try:
            response = requests.get(api.format(gt, challenge), timeout=20).text
            res_dict = json.loads(response)
            if res_dict['status'] != 'ok':
                print('验证失败:服务器验证失败')
                return '',''
            return (res_dict['challenge'], res_dict['validate'])
        except Exception as e:
            return print('极验破解失败', e)

    # 登录
    def login(self, headers, gt_challenge, gt_validate):
        data = {
            'geetest_challenge': gt_challenge,
            'geetest_validate': gt_validate,
            'geetest_seccode': gt_validate + '|jordan',
            'user_name': '18328542325',
            'user_pswd': 'admin123',
        }
        a = self.RequestHelper.get(url='http://httpbin.org/ip', headers=headers, proxy=self.proxies)
        print('登录', a)
        response = self.RequestHelper.post(
            url='https://ss.cods.org.cn/usercenter/validateLogin',
            data=data,
            headers=headers,
            # proxy=config.proxyMeta,
            # proxy='114.234.80.241:23987',
            proxy=self.proxies,
            timeout=10)
        print(headers)
        print('登录结果',response)
        if response is None:
            return
        if '0' not in response:
            print('登录失败:{}'.format('1'))
            return False
        return True

    # 详情页请求
    def detial(self, url, headers):
        # response = self.RequestHelper.get(url, headers=headers, proxy=config.proxyMeta)
        # response = self.RequestHelper.get(url, headers=headers, proxy='114.234.80.241:23987')
        response = self.RequestHelper.get(url, headers=headers, proxy=self.proxies)
        print(response)

    def run(self):
        # self.proxies = config.proxyMeta
        self.proxies = '1.199.155.39:20455'
        
        start = time.time()
        headers = deepcopy(self.headers)
        headers['Proxy-Tunnel'] = str(self.ProxyTunnel)
        # self.ProxyTunnel += 1
        jsessionid = self.probe(headers)
        print('初次访问耗时:', time.time() - start)
        if jsessionid is None:
            return
        headers['Cookie'] = 'JSESSIONID={}'.format(jsessionid)
        print(headers)
        jiyan = self.get_jiyan_param(headers)
        print(jiyan)
        print('获取jessionid耗时:', time.time() - start)
        if jiyan is None:
            return
        (gt, challenge) = jiyan
        print('jiyan:',jiyan)
        (challenge, validate) = self.jiyan_crack(gt, challenge)
        if challenge =='':
            return
        print('解密耗时:', time.time() - start)
        print('challenge:', challenge, 'validate:', validate)
        if self.login(headers, challenge, validate):

            self.detial(
                url='https://ss.cods.org.cn/latest/detail?jgdm=468d0d89d196932ecbb9c90060ec7e7e',
                headers=headers
            )

if __name__ == '__main__':
    start = CodeApi()
    start.run()
