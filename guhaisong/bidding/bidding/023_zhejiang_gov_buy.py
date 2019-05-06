import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
import threading
import datetime
import hashlib
import pymongo
from utils.zb_storage_setting import StorageSetting
from utils.redis_tool import Rdis_Queue
import re
from utils.cpca import *
import time
from six.moves import queue
from utils import proxy_pool


class GovBuy(object):
    '''浙江政府采购网'''
    def __init__(self):
        name = 'zhejiang_manager_zjzfcg_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://www.zjzfcg.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://www.zjzfcg.gov.cn/purchaseNotice/index.html?categoryId=10',
            'Connection': 'keep-alive',
        }


        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='zhejinag_list1', dbset='zhejiang_set1')

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

    def load_get_html(self,data_dict):
        try:
            proxies = proxy_pool.proxies ()
            params = {
                'noticeId':data_dict['id'],
                'url': 'http://notice.zcy.gov.cn/new/noticeDetail',
            }
            url = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults'
            response = requests.get(url=url, headers=self.headers,params=params,proxies=proxies)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = data_dict['title']
            # print(title)
            status = data_dict['typeName']
            # print(status)

            _id = self.hash_to_md5(response.url)

            publish_date = time.strftime("%Y-%m-%d",time.localtime(int(data_dict['pubDate']) /1000))
            # print(publish_date)

            area_name = data_dict['districtName']
            # print(area_name)

            source = 'http://www.zjzfcg.gov.cn/'
            try:
                content_html = response.json()['noticeContent']
            except:
                return

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
            retult_dict['zh_name'] = '浙江政府采购网'
            retult_dict['en_name'] = 'Zhejiang government Procurement'

            print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            params = {
                'pageSize': '15',
                'pageNo': page,
                'url': 'http://notice.zcy.gov.cn/new/noticeSearch',
                'noticeType': '0',
            }
            url = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults'
            proxies = proxy_pool.proxies ()
            response = requests.get(url=url, headers=self.headers,params=params,proxies=proxies,timeout=5).json()
        except Exception as e:
            print('load_post error{}'.format(e))
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            response_li = response['articles']
            # print(response_li)
            for data_dict in response_li:
                self.load_get_html(data_dict)

                # self.load_get_html(data_dict)
                # if not self.rq.in_rset(urls):
                #     self.rq.add_to_rset(urls)
                #     self.rq.pull_to_rlist(urls)

    def init(self):
        count = 8
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            try:
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        # threading.Thread(target=self.init).start()
        task_li = [
                {'all_page': 3},
                # {'all_page': 2000},

            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # url =task['url']+str(page)+'.html'
                    # self.load_get(page)
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()





