#coding:utf-8
import requests
from lxml import etree
import time
import datetime
import hashlib
import pymongo
from utils.zb_storage_setting import StorageSetting
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
import os
from utils import proxy_pool


class GovBuy(object):
    '''济南政府采购网'''
    def __init__(self):
        name = 'jinan_jncz_jinan_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Proxy-Connection': 'keep-alive',
            'Proxy-Authorization': 'Basic MTYzOTY2MzE2ODphamxhNTJ0bQ==',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': 'http://119.164.253.173:8080/jngp2016/site/list.jsp?curpage=3&colid=121',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='jinan_list1', dbset='jinan_set1')

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

    def load_get_html(self, tr):

        if tr == None:
            return
        try:
            selector_li = etree.HTML(str(tr))
            tr_li = selector_li.xpath('//tr/td[2]/a/@href')[0]
            url = 'http://119.164.253.173:8080' + tr_li
            proxies = proxy_pool.proxies ()
            response = requests.get(url=url, headers=self.headers,proxies=proxies,timeout=10).content.decode('gb18030')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # self.load_get_html(li)
        else:
            title = selector_li.xpath('//tr/td[2]/a/text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',title[0])
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'
            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            publish_date = selector_li.xpath('//tr/td/text()')
            if publish_date != []:
                publish_date = re.sub(r'\[|\]','-',re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group())
            else:
                publish_date = None
            # print(publish_date)
            area_name = '山东-济南'

            source = 'http://jncz.jinan.gov.cn/'

            try:
                table_ele  = selector.xpath('//body/table')
            except:
                return
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
            retult_dict['zh_name'] = '济南市财政局'
            retult_dict['en_name'] = 'Jinan Finance Bureau'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,colid, page):
        try:
            params = (
                ('curpage', page),
                ('colid', colid),
            )
            url = 'http://119.164.253.173:8080/jngp2016/site/list.jsp'
            proxies = proxy_pool.proxies ()
            response = requests.get(url=url, headers=self.headers, params=params,proxies=proxies,timeout=10).content.decode('gb18030')
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(colid,page)
        else:
            print('第{}页'.format(page))
            try:
                li_ele_li = selector.xpath('//table[@class="list"]/tr')
            except:
                return
            for li_ele in li_ele_li:
                tr = etree.tostring(li_ele, pretty_print=True, encoding='utf-8', method='html').decode('utf-8')
                # print(li)
                self.load_get_html(tr)

    def run(self):
        task_li = [
                {'colid': '37', 'all_page': 3},
                {'colid':'38', 'all_page': 3},
                {'colid':'81', 'all_page': 3},
                {'colid':'29', 'all_page': 3},
                {'colid':'101', 'all_page': 3},
                {'colid':'122', 'all_page': 3},


            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    colid = task['colid']
                    self.load_get(colid, page)
                    # spawns = [gevent.spawn(self.load_get,colid, page + i) for i in range(count)]
                    # gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
