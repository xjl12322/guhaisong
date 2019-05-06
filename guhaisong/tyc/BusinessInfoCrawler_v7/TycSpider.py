# coding=utf-8
import time
import config
from copy import deepcopy
from PublicTools import TokenPool
from PublicTools import RequestTools
from PublicTools import ParseTools
from PublicTools import MongoHelper

class spider:
    def __init__(self):
        self.login_headers = {
            'Host': 'www.tianyancha.com',
            'Accept': '*/*',
            'Origin': 'https://www.tianyancha.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
            'Content-Type': 'application/json; charset=UTF-8',
            'Referer': 'https://www.tianyancha.com/',
        }
        
        self.other_headers = {
            'Host': 'www.tianyancha.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
            'Accept': '*/*',
            'Referer': 'https://www.tianyancha.com/',
        }
        self.tyc_token_api = TokenPool.GetToken()
        self.MHelper = MongoHelper.Helper()
        self.request = RequestTools.RequestHelper()
        self.ParseHelper = ParseTools.ParseHelper()

    # 全局搜索模块
    def search(self, token, keyword):
        header = deepcopy(self.other_headers)
        header['Cookie'] = 'auth_token={};'.format(token)
        return self.request.get(url=config.search_api.format(keyword), headers=header)

    # 详情页模块
    def detail(self, token, keyword):
        header = deepcopy(self.other_headers)
        header['Cookie'] = 'auth_token={};'.format(token)
        return self.request.get(url=config.detail_api.format(keyword,allow_redirects=None), headers=header)

    # 分支机构模块
    def branch(self, token, keyword):
        items, item = [], {}
        header = deepcopy(self.other_headers)
        header['Cookie'] = 'auth_token={};'.format(token)
        response = self.request.get(url=config.branch_api.format(1, keyword), headers=header)
      
        if response ==None:
            return
        # 账号封禁
        if '禁止访问' in response:
            return
        # 返回长度过短，无数据
        if response is None or len(response) < 40:
            return items
        # response
        (pagenum, res) = self.ParseHelper.branch_parse(response)
        items = items + res
        for pn in range(1, pagenum):
            response = self.request.get(url=config.branch_api.format(pn, keyword), headers=header)
            if '禁止访问' in response or response is None or len(response) < 40:
                continue
            page, res = self.ParseHelper.branch_parse(response)
            items = items + res
        return items

    # 股东模块
    def stockholder(self, token, keyword):
        items, item = [], {}
        header = deepcopy(self.other_headers)
        header['Cookie'] = 'auth_token={};'.format(token)
        response = self.request.get(url=config.stockholder_api.format(1, keyword), headers=header)
        # 账号封禁
        if '禁止访问' in response:
            return
        # 返回长度过短，无数据
        if response is None or len(response) < 40:
            return items
        (pagenum, res) = self.ParseHelper.stockholder_parse(response)
        items = items + res
        for pn in range(1, pagenum):
            response = self.request.get(url=config.stockholder_api.format(pn, keyword), headers=header)
            if '禁止访问' in response or response is None or len(response) < 40:
                continue
            (page, res) = self.ParseHelper.stockholder_parse(response)
            items = items + res
        return items

    # 对外投资模块
    def investment(self, token, keyword):
        items, item = [], {}
        header = deepcopy(self.other_headers)
        header['Cookie'] = 'auth_token={};'.format(token)
        response = self.request.get(url=config.investment_api.format(1, keyword), headers=header)
        # 账号封禁
        if '禁止访问' in response:
            return
        # 返回长度过短，无数据
        if response is None or len(response) < 40:
            return items
        (pagenum, res) = self.ParseHelper.investment_parse(response)
        items = items + res
        for pn in range(1, pagenum):
            response = self.request.get(url=config.investment_api.format(pn, keyword), headers=header)
            if '禁止访问' in response or response is None or len(response) < 40:
                continue
            (page, res) = self.ParseHelper.investment_parse(response)
            items = items + res
        return items

    # 年报模块
    def annualreport(self, user, token, keyword):
        items = []
        header = deepcopy(self.other_headers)
        header['Cookie'] = 'auth_token={};'.format(token)
        for year in range(int(time.strftime("%Y")) - 3, int(time.strftime("%Y"))):
            response = self.request.get(url=config.annualreport_api.format(keyword, year), headers=header)
            # 返回长度过短，无数据
            if response is None or '页面丢了' in response:
                continue
            # 账号封禁
            if '请输入手机号' in response:
                self.tyc_token_api.black(tel=user,black='Y',state='')  # 拉黑处理
                return items
            item = self.ParseHelper.annualreport_parse(response)
            item['year'] = year
            items.append(deepcopy(item))
        return items

    def run(self, mode, keyword, times=0):
        token_dic = self.tyc_token_api.get_token()
        tel,token = token_dic['tel'],token_dic['token']
        
        # ---------全局搜索模式:公司名称、手机号、老板名称、信用代码、注册代码、邮箱,商标名称-----------------
        if mode == 'list':
            response = self.search(token, keyword)
            # response 出现问题,5次重复请求
            if response is None or len(response) < 100:
                return self.run(mode, keyword, times + 1) if times <= 5 else {
                    'code': '10501',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            if '请输入手机号' in response:
                self.tyc_token_api.black(tel=tel,black='Y',state='')  # 拉黑处理
                return self.run(mode, keyword, times + 1) if times <= 50 else {
                    'code': '10502',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            # 正常结果,开始解析内容
            items = self.ParseHelper.list_parse(response)
            # 存储
            [self.MHelper.push(
                collection=config.mongo_list_collection, item=item, key=item['company_id']) for item in items]
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': items
            }
        # --------------------------------详情页  仅限天眼查内部id---------------------------------
        elif mode == 'detail':
            if not str(keyword).isdigit():
                return {
                    'code': '10502',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            response = self.detail(token, keyword)
            # response 出现问题,5次重复请求
            if response is None or len(response) < 100:
                return self.run(mode, keyword, times + 1) if times <= 5 else {
                    'code': '10501',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            
            if '请输入手机号' in response:
                self.tyc_token_api.black(tel=tel,black='Y',state='')  # 拉黑处理
                return self.run(mode, keyword, times + 1) if times <= 50 else {
                    'code': '10503',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            
            # 正常结果,开始解析内容
            items = self.ParseHelper.detail_parse(keyword, response)
            # 存储
            self.MHelper.push(collection=config.mongo_detail_collection, item=items, key=items['company_id'])
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': [items]
            }
        # --------------------------------分支机构 仅限天眼查内部id---------------------------------
        elif mode == 'branch':
            if not str(keyword).isdigit():
                return {
                    'code': '10502',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            items = self.branch(token, keyword)
            # response 出现问题,5次重复请求
            if items is None:
                self.tyc_token_api.black(tel=tel,black='Y',state='')  # 拉黑处理
                return self.run(mode, keyword, times + 1) if times <= 5 else {
                    'code': '10501',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            # 存储
            for item in items:
                item['parent_id'] = keyword
                self.MHelper.push(collection=config.mongo_branch_collection, item=item, key=item['branch_company_id'])
            # 正常结果,开始解析内容
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': items
            }
        # --------------------------------股东信息 仅限天眼查内部id---------------------------------
        elif mode == 'stockholder':
            if not str(keyword).isdigit():
                return {
                    'code': '10502',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            items = self.stockholder(token, keyword)
            # items 出现问题,5次重复请求
            if items is None:
                self.tyc_token_api.black(tel=tel,black='Y',state='')  # 拉黑处理
                return self.run(mode, keyword, times + 1) if times <= 5 else {
                    'code': '10501',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            # 存储
            for item in items:
                item['company_id'] = keyword
                self.MHelper.push(collection=config.mongo_stockholder_collection, item=item, key=(item['holder_id']))
            # 正常结果,开始解析内容
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': items
            }
        # --------------------------------对外投资 仅限天眼查内部id---------------------------------
        elif mode == 'investment':
            if not str(keyword).isdigit():
                return {
                    'code': '10502',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            items = self.investment(token, keyword)
            # response 出现问题,5次重复请求
            if items is None:
                self.tyc_token_api.black(tel=tel,black='Y',state='')  # 拉黑处理
                return self.run(mode, keyword, times + 1) if times <= 5 else {
                    'code': '10501',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            # 存储
            for item in items:
                item['investor_id'] = keyword
                self.MHelper.push(collection=config.mongo_investment_collection, item=item, key=(
                        str(item['investor_id']) + '-' + str(item['invested_company_id'])))
            # 正常结果,开始解析内容
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': items
            }

        # --------------------------------年报信息 仅限天眼查内部id---------------------------------
        elif mode == 'annualreport':
            if not str(keyword).isdigit():
                return {
                    'code': '10502',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            items = self.annualreport(tel, token, keyword)
            # response 出现问题,5次重复请求
            if items is None:
                return self.run(mode, keyword, times + 1) if times <= 5 else {
                    'code': '10501',
                    'keys': keyword,
                    'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                    'info': 'error'
                }
            # 存储
            for item in items:
                item['company_id'] = keyword
                self.MHelper.push(collection=config.mongo_annualreport_collection, item=item, key=(
                        str(item['year']) + '-' + str(item['company_id'])))
            # 正常结果,开始解析内容
            return {
                'code': '10200',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': items
            }
        # 模式错误
        else:
            return {
                'code': '10505',
                'keys': keyword,
                'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': 'error'
            }


if __name__ == '__main__':
    start = spider()
    from pprint import pprint

    pprint(start.run(mode='list', keyword='成都川远鸣松精密模具有限公司'))
    # pprint(start.run(mode='detail', keyword='3174100'))
