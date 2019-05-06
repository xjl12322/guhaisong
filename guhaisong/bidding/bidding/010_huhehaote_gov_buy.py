import requests
from lxml import etree
from six.moves import queue
import threading
import datetime
import hashlib
import pymongo
import gevent
from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
from utils.cpca import *
import time
from utils.zb_storage_setting import StorageSetting


class GovBuy(object):
    '''呼和浩特政府采购网'''
    def __init__(self):
        name = 'huheaote_hhgp_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://www.hhgp.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*',
            'Referer': 'http://www.hhgp.gov.cn/huShi_web_login',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Content-Length': '0',
        }


        self.rq = Rdis_Queue(host='localhost', dblist='huhehaote_list1', dbset='huhehaote_set1')


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

    def load_get(self,params):
        try:
            url = 'http://www.hhgp.gov.cn/huShi_web_login/showAllMessage'
            response = requests.post(url=url, headers=self.headers,params=params).json()
            response_str = response['0']
            selector = etree.HTML(response_str)
        except:
            print('load_post error')
        else:
            url_li = selector.xpath('//li/span[1]/a/@href')
            for url in url_li:
                url = 'http://www.hhgp.gov.cn'+ url
                if not self.rq.in_rset(url):
                    self.rq.add_to_rset(url)
                    self.rq.pull_to_rlist(url)

    def load_get_html(self,url):
        try:
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:'.format(e))
        else:
            # print(response)
            _id = self.hash_to_md5(url)
            title = selector.xpath('//*[@id="content"]/div/div[2]/div/div/h1/text()')
            if title != []:
                title = title[0]
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'
            publish_date = selector.xpath('//*[@id="content"]/div/div[2]/div/div/i/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d+\-\d+\-\d+)',publish_date[0]).group()
            else:
                publish_date = None
            # print(publish_date)
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='content')
            # print(content_html)
            source = 'http://www.hhgp.gov.cn/'
            area_name = self.get_area('呼和浩特',title)

            # print(content)
            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['publish_date'] = publish_date
            retult_dict['source'] = source
            retult_dict['area_name'] = area_name

            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '呼和浩特市政府采购网 '
            retult_dict['en_name'] = 'Huhhot City Government Procurement'

            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)


    def init(self):
        count = 6
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            try:
                # self.load_get_html(self.rq.get_to_rlist())
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        threading.Thread(target=self.init).start()
        task_li = [
                # {'code':'265.266.304', 'all_page': 29},
                # {'code':'265.266.269', 'all_page': 70},
                # {'code':'265.266.270', 'all_page': 67},
                # {'code':'265.266.271', 'all_page': 217},
                # {'code':'265.266.303', 'all_page': 58},
                # {'code':'265.266.404', 'all_page': 1},
                # {'code':'265.266.403', 'all_page': 14},
                # {'code':'265.266.343', 'all_page': 21},
                {'code':'265.266.304', 'all_page': 1},
                {'code':'265.266.269', 'all_page': 1},
                {'code':'265.266.270', 'all_page': 1},
                {'code':'265.266.271', 'all_page': 1},
                {'code':'265.266.303', 'all_page': 1},
                {'code':'265.266.404', 'all_page': 1},
                {'code':'265.266.403', 'all_page': 1},
                {'code':'265.266.343', 'all_page': 1},
            ]
        for task in task_li:
            for page in range(1,task['all_page'] + 1):
                params = (
                    ('code', task['code']),
                    ('pageNo', str(page)),
                    ('check', '1'),
                )
                self.load_get(params)
                print('第{}页'.format(page))

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
