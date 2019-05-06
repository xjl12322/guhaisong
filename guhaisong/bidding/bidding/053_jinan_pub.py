import gevent
from gevent import monkey
monkey.patch_all()
from lxml import etree
import time
import datetime
import hashlib
import pymongo

import requests
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting
import json

class GovBuy(object):
    '''济南公共资源交易信息网'''
    def __init__(self):
        name = 'jinan_jngp_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'jnggzy.jinan.gov.cn',
            'Origin': 'http: // jnggzy.jinan.gov.cn',
            'Referer': 'http: // jnggzy.jinan.gov.cn / jnggzyztb / front / noticelist.do?type = 1 & xuanxiang = 1 & area =',
        }

        self.rq = Rdis_Queue(host='localhost', dblist='jinan_jngp_gov_cn_list1', dbset='jinan_jngp_gov_cn_set1')

    def is_running(self):
        is_runing = True
        if self.rq.r_len() == 0 and len (self.rq.rset_info()) > 0:
            return False
        else:
            return is_runing

    def hash_to_md5(self, sign_str):
        m = hashlib.md5()
        sign_str = sign_str.encode('utf-8')
        m.update(sign_str)
        sign = m.hexdigest()
        return sign

    def now_time(self):
        time_stamp = datetime.datetime.now()
        return time_stamp.strftime('%Y-%m-%d %H:%M:%S')

    def save_to_mongo(self,result_dic):
        self.coll.saves(result_dic)
        self.is_running()

    def get_area(self,pro, strs):
        location_str = [strs]
        try:
            df = transform(location_str, umap={})
            area_str = re.sub(r'省|市', '-', re.sub(r'省市区0', '', re.sub(r'/r|/n|\s', '', str(df))))
        except:
            pass
        else:
            if area_str == '':
                area_li = [pro]
            else:
                area_li = (area_str.split('-'))
            if len(area_li) >=2 and area_li[1] !='':
                return '-'.join(area_li[:2])
            else:
                return area_li[0]

    def load_get_html(self, url):
        if url == None:
            return
        try:
            # selector_div = etree.HTML(str(div))
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # print(url)
            # self.load_get_html(url)
        else:
            # print(url)
            title = selector.xpath('//div[@class="list"]/h1//text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',''.join(title))
                try:
                    status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)
            publish_date = selector.xpath('//div[@class="list"]/div/span//text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            else:
                publish_date = None
            area_name = '山东-济南'
            # print(area_name)
            source = 'http://jnggzy.jinan.gov.cn/'

            table_ele  = selector.xpath('//div/div[@class="list"]')
            if table_ele != []:
                table_ele = table_ele[0]
            else:
                return
            content_html = etree.tostring(table_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['area_name'] = area_name
            retult_dict['source'] = source

            retult_dict['publish_date'] = publish_date

            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '济南公共资源交易中心'
            retult_dict['en_name'] = 'Jinan Public resource'

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        try:
            params = {
            'area':'',
            'type':types,
            'xuanxiang': categoryId,
            'subheading':'',
            'pagenum': page,
            }

            url = 'http://jnggzy.jinan.gov.cn/jnggzyztb/front/search.do'
            response = requests.post(url=url, headers=self.headers, data=params).json()
            response_str = response['params']['str']
            selector = etree.HTML(response_str)
        except Exception as e:
            print('load_get error:{}'.format(e))
            # time.sleep(3)
            # self.load_get(categoryId, types, page)
        else:
            print(response)
            print('第{}页'.format(page))
            id_li = selector.xpath('//ul/li/a/@onclick')
            if len(id_li) > 0:
                iid_li = [re.sub(r'.*?\(|\).*','',i) for i in id_li]
                for iid in iid_li:
                    url = 'http://jnggzy.jinan.gov.cn/jnggzyztb/front/showNotice.do?iid={}&xuanxiang={}'.format(iid, categoryId)
                    # self.load_get_html(url)
                    if not self.rq.in_rset(url):
                        self.rq.add_to_rset(url)
                        self.rq.pull_to_rlist(url)
            else:
                url_li = selector.xpath ('//ul/li/a/@href')
                for url in url_li:
                    urls = 'http://jnggzy.jinan.gov.cn' + url
                    # self.load_get_html(urls)
                    if not self.rq.in_rset(urls):
                        self.rq.add_to_rset(urls)
                        self.rq.pull_to_rlist(urls)


    def init(self):
        count = 2
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            try:
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        threading.Thread(target=self.init).start()
        task_li = [
                {'categoryId':'招标公告', 'types':'1','all_page': 4},
                {'categoryId':'中标公示', 'types':'1','all_page': 4},
                {'categoryId':'变更公告', 'types':'1','all_page': 4},
                {'categoryId':'废标公告', 'types':'1','all_page': 4},
            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    categoryId = task['categoryId']
                    types = task['types']

                    spawns = [gevent.spawn(self.load_get, categoryId, types, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
