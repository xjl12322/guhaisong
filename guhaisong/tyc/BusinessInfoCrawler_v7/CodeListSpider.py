# coding=utf-8
import re
import time
import json
import config
from PublicTools import ParseTools
from urllib.parse import quote
from PublicTools import MongoHelper
from PublicTools import RequestTools
from PublicTools.PrivateHead import PrivateHead

class CodeApi:
    def __init__(self):
        self.PrivateHead = PrivateHead()
        self.BaseUrl = 'https://ss.cods.org.cn'
        self.SignUrl = 'http://www.cods.org.cn/portal/checkData'
        self.TokenUrl = 'https://ss.cods.org.cn/isearch'
        self.RequestHelper = RequestTools.RequestHelper()
        self.ParseHelper = ParseTools.ParseHelper()
        self.MHelper = MongoHelper.Helper()

    def CookieParam(self):
        self.cookie = False
        self.RequestHelper.get(self.BaseUrl, timeout=10)
        cookies_tuple = self.RequestHelper.cookies
        if cookies_tuple is None:
            return
        try:
            self.cookie = 'userCookie={}'.format(cookies_tuple[1][1])
            print('cookie-->',self.cookie)
            return True
        except Exception as e:
            return print(e)

    def SignParam(self):
        self.sign, headers = False, self.PrivateHead.SignHead()
        data = {'type': '1', 'keywords': quote(str(self.keyword))}
        # res = self.RequestHelper.post(self.SignUrl, data=data, headers=headers, timeout=10, proxy=config.proxyMeta)
        res = self.RequestHelper.post(self.SignUrl, data=data, headers=headers, timeout=10)
        self.sign = json.loads(res)['payload'] if 'payload' in res else None if res is not None else None
        print('sign-->',self.sign)
        return False if self.sign is None else True

    def TokenParam(self):
        self.token, headers = False, self.PrivateHead.TokenHead()
        headers['Cookie'] = self.cookie
        data = {'jsonString': '{"type":"1","keywords":"%s"}' % quote(self.keyword), 'sign': self.sign}
        response = self.RequestHelper.post(self.TokenUrl, data=data, headers=headers, timeout=10)
        # response = self.RequestHelper.post(self.TokenUrl, data=data, headers=headers, timeout=10, proxy=config.proxyMeta)
        temp = re.findall('searchToken=(.*?)"', response) if response is not None else None
        print(temp)
        self.token = None if temp is None else temp[0] if len(temp) != 0 else None
        print('token',self.token)
        return False if self.token is None else True if len(self.token) != 0 else False

    def run(self, keyword):
        self.keyword = keyword
        headers = self.PrivateHead.SearchHead()
        # if not self.CookieParam() or not self.SignParam() or not self.TokenParam():
        #     return {
        #         'code': '10500',
        #         'keys': keyword,
        #         'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
        #         'info': 'Parameter incomplete'
        #     }
        self.CookieParam()
        self.SignParam()
        self.TokenParam()
        
        url = self.BaseUrl + '/latest/searchR?q={}&t=common&currentPage=1&searchToken={}'.format(
            quote(quote(keyword)), self.token)
        headers['Cookie'] = self.cookie
        response = self.RequestHelper.get(url, headers=headers, timeout=10)

        # 非法请求
        if '抱歉，找不到页面啦' in response or '非法请求，请在检索框内输入关键词查询' in response or '代理ip' in response:
            return {
                'code': '10501',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': 'Unlawful request'
            }
        # 查询不到
        if '暂无搜索数据' in response or '检索词范围过大' in response:
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': []
            }
        # 正常数据
        items = self.ParseHelper.code_parse(response)
        for item in items:
            self.MHelper.push(collection=config.mongo_code_search_collection, item=item, key=(item['code']))
        return {
            'code': '10200',
            'keys': keyword,
            'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': items
        }


if __name__ == '__main__':
    start = CodeApi()
    response = start.run('土豆')
    from pprint import pprint

    pprint(response)
