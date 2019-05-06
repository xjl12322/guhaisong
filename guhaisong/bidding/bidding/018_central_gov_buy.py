#coding:utf-8
import requests
from lxml import etree
import threading
import datetime
import hashlib
import pymongo
from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
from utils.cpca import *
from six.moves import queue
import time
import os
import sys
import signal
from utils import proxy_pool
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''中央政府采购网'''
    def __init__(self):
        name = 'center_zycg_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        
        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/535.19',
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html, */*',
            # 'Referer': 'http://www.zycg.gov.cn/article/article_search?catalog=StockAffiche&keyword=&page=2',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'If-None-Match': 'a872927a5615e69c3447de47a43544aa',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='central_list1', dbset='central_set1')

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

    def load_get_html(self,li):
        sele_li = etree.HTML (li)
        time.sleep(0.5)
        # url = 'http://www.zycg.gov.cn/article/show/311865'
        if li == None:
            return
        try:
            url_li = sele_li.xpath('//li/a/@href')
            url = 'http://www.zycg.gov.cn' + url_li[0]
            # url = 'http://www.zycg.gov.cn/article/show/527813'
            proxies = proxy_pool.proxies ()
            response = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=10).text
            selector = etree.HTML (response)
            if '打印预览' in response:
                url_li = selector.xpath('//span[@id="btnPrint"]/a/@href')
                url = 'http://www.zycg.gov.cn' + url_li[0]
                response = requests.get (url=url, headers=self.headers, proxies=proxies, timeout=10).text
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            self.rq.pull_to_rlist(li)
        else:
            print(url)
            title = sele_li.xpath('//li/a/@title')
            if title != []:
                title = re.sub(r'\r|\n|\s','',''.join(title))
            else:
                title = ''
            try:
                status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
            except:
                status = '公告'

            _id = self.hash_to_md5(url)

            publish_date = sele_li.xpath('//li/span/text()')
            if publish_date != []:
                publish_date = re.sub (r'\r|\n|\s|\[|\]', '', ''.join (publish_date))
            else:
                publish_date = ''
            
            print(publish_date,title)
            
            # print(response)
            
            soup = BeautifulSoup(response)
            
            content_html = soup.find(class_="detail_gg")
            if content_html == None:
                content_html = soup.find(class_='frame-pane')
                if content_html ==None:
                    content_html = soup.find(name='Frm_Order')
                    if content_html == None:
                        print(content_html)
                        return
            
            # print('content_html',content_html)
            # print(response)
            
            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['area_name'] = '中央'
            retult_dict['source'] = 'http://www.zycg.gov.cn/'

            retult_dict['publish_date'] = publish_date

            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '中央政府采购网'
            retult_dict['en_name'] = 'Central Government Procurement'

            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)

    def load_get(self, page):
        try:
            params = {
                'category_id':'',
                'keyword':'',
                'page': str(page),
                'px': '2'}
            
            url = 'http://www.zycg.gov.cn/article/article_search'
            proxies = proxy_pool.proxies ()
            response = requests.post(url=url, headers=self.headers, params=params,proxies=proxies,timeout=10).text
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(page)
        else:
            li_ele_li = selector.xpath('//ul[@class="lby-list"]/li')
            print('第{}页'.format(page))
            for li_ele in li_ele_li:
                li = etree.tostring(li_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
                self.load_get_html(li)

    def run(self):
        task_li = [
                {'all_page': 30},
            ]
        count = 1
        for task in task_li:
            try:
                for page in range(1, task['all_page'] + 1, count):
                    self.load_get(page)
                #     spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                #     gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()

