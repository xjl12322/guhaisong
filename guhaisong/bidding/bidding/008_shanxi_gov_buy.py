
import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
from six.moves import queue
import threading
import datetime
import hashlib
import pymongo
from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
import time
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting


class GovBuy(object):
    '''山西政府采购网'''
    def __init__(self):
        name = 'shanxi_ccgp-shanxi_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': 'http://www.ccgp-shanxi.gov.cn/view.php?nav=104',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.rq = Rdis_Queue(host='localhost', dblist='shanxi_list1', dbset='shanxi_set1')



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
            url = 'http://www.ccgp-shanxi.gov.cn/view.php'
            response = requests.post(url=url, headers=self.headers,params=params).content.decode('utf-8')

            selector = etree.HTML(response)
            url_li = selector.xpath('//*[@id="node_list"]/tbody/tr/td[1]/a/@href')
        except:
            print('load_post error')
        else:
            # print(url_li)
            if url_li != []:
                for url in url_li:
                    url ='http://www.ccgp-shanxi.gov.cn/' + url
                    if not self.rq.in_rset(url):
                    #     pass
                        self.rq.add_to_rset(url)
                        self.rq.pull_to_rlist(url)

    def load_get_html(self,url):
        try:
            # print(url)
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except:
            print('laod_get_html error')
        else:
            # print(response)
            _id = self.hash_to_md5(url)
            # # print(_id)
            title = selector.xpath('//tr[@class="bk5"]/td/table/tr/td/table/tr/td/div/h2/text()')
            if title != []:
                title = title[0]
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'
            # print(title)
            publish_date = selector.xpath('//tr[@class="bk5"]/td/table/tr[2]/td//text()')
            # print(publish_date)
            if publish_date != []:
                publish_date = re.search(r'(\d+年\d+月\d+日)',publish_date[2])
                if publish_date != []:
                    publish_date = publish_date[0]
                else:
                    publish_date = None
            else:
                publish_date = None
            # print(publish_date)
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='bk5')
            # print(content_html)

            source = 'http://www.ccgp-shanxi.gov.cn/'
            area_name =self.get_area('山西',title)
            #
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
            retult_dict['zh_name'] = '中国山西政府采购'
            retult_dict['en_name'] = 'Shanxi Government Procurement'
            #
            # print(retult_dict)
            #
            print('列表长度为={}'.format(self.rq.r_len()))
            #
            self.save_to_mongo(retult_dict)


    def init(self):
        count = 6
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
            gevent.joinall(spawns)

    def run(self):
        threading.Thread(target=self.init).start()
        task_li = [
            #{'nav':100, 'end_page':14705,'status':'招标公告'},
            #{'nav':104, 'end_page':13667,'status':'结果公告'},
            #{'nav':105, 'end_page':2291,'status':'变更公告'},
            #{'nav':116, 'end_page':747,'status':'单一来源公告'},
            #{'nav':131, 'end_page':249,'status':'招标预公告'},
            #{'nav':132, 'end_page':1,'status':'邀请公告'},
            #{'nav':153, 'end_page':7279,'status':'合同公告'},
             {'nav':100, 'end_page':4,'status':'招标公告'},
             {'nav':104, 'end_page':3,'status':'结果公告'},
             {'nav':105, 'end_page':2,'status':'变更公告'},
             {'nav':116, 'end_page':2,'status':'单一来源公告'},
             {'nav':131, 'end_page':1,'status':'招标预公告'},
             {'nav':132, 'end_page':1,'status':'邀请公告'},
             {'nav':153, 'end_page':1,'status':'合同公告'},
        ]
        for task in task_li:
            for page in range(1,task['end_page'] + 1):
                params = {
                    'app':'',
                    'type':'',
                    'nav': task['nav'],
                    'page': str(page)
                }
                self.load_get(params)
                print('第{}页'.format(page))

    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
