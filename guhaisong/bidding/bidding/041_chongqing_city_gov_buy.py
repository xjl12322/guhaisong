import gevent
from gevent import monkey
monkey.patch_all()
from lxml import etree
import time
import datetime
import hashlib
import pymongo
from utils.zb_storage_setting import StorageSetting
import requests
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
from utils import proxy_pool
from six.moves import queue

class GovBuy(object):
    '''重庆政府采购网'''
    def __init__(self):
        name = 'chongqing_cqgp_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.cqgp.gov.cn/notices/list?source=41,42^&area=^%^E9^%^87^%^8D^%^E5^%^BA^%^86^%^E5^%^B8^%^82^&purches=^%^E9^%^87^%^87^%^E8^%^B4^%^AD^%^E5^%^85^%^AC^%^E5^%^91^%^8A',
            'Connection': 'keep-alive',
        }

        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='chongqing_list1', dbset='chongqing_set1')

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

    def load_get_html(self, pid):
        if pid == None:
            return
        try:
            proxies = proxy_pool.proxies ()
            url = 'https://www.cqgp.gov.cn/gwebsite/api/v1/notices/stable/{}'.format(pid)
            response = requests.get(url=url, headers=self.headers,proxies=proxies,timeout=10).json()
            # selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            self.load_get_html(pid)
        else:
            title = response['notice']['title']
            try:
                status = response['notice']['projectPurchaseWayName']
            except:
                status = '公告'
            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            # publish_date = selector.xpath('//div[@class="content_about"]/span[2]/em/text()')
            publish_date = response['notice']['issueTime']
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',publish_date).group()
            else:
                publish_date = None
            # print(publish_date)
            area_name = '重庆'

            # print(area_name)

            source = 'https://www.cqgp.gov.cn/'

            content_html = response['notice']['html']

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
            retult_dict['zh_name'] = '重庆市政府采购网'
            retult_dict['en_name'] = 'Chongqing City Government Procurement'
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            params = (
                ('pi', page),
                ('ps', '20'),
                ('timestamp', str(int(time.time()*1000))),
            )
            proxies = proxy_pool.proxies ()
            url = 'https://www.cqgp.gov.cn/gwebsite/api/v1/notices/stable'
            response = requests.get(url=url, headers=self.headers, params=params, proxies=proxies,timeout=5).json()
            # selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            response_li = response['notices']
            for data_dict in response_li:
                pid = data_dict['id']
                # print(pid)
                # self.load_get_html(pid)
                # time.sleep(2)
                if not self.rq.in_rset(pid):
                    self.rq.add_to_rset(pid)
                    self.rq.pull_to_rlist(pid)

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
        # print(os.getppid())
        threading.Thread(target=self.init).start()
        task_li = [

                # {'all_page': 18647},
                {'all_page': 3},
            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # self.load_get(types, page)
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()





