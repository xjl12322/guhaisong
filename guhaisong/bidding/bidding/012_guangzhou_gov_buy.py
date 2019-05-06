import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
from six.moves import queue
import threading
import datetime
import hashlib
import pymongo
from utils.zb_storage_setting import StorageSetting
from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
from utils.cpca import *
import time

class GovBuy(object):
    '''广州政府采购网'''
    def __init__(self):
        name = 'guangzhou_gzg2b_gzfinance_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://gzg2b.gzfinance.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Referer': 'http://gzg2b.gzfinance.gov.cn/gzgpimp/portalindex.do?method=goInfogsgg^&linkId=gsgg',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }


        self.rq = Rdis_Queue(host='localhost', dblist='guangzhou_list1', dbset='guangzhou_set1')



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


    def load_get(self,data):
        try:
            url = 'http://gzg2b.gzfinance.gov.cn/gzgpimp/portalsys/portal.do'
            params = (
                ('method', 'queryHomepageList'),
                ('t_k', 'null'),
            )
            response = requests.post(url=url, headers=self.headers,params=params,data=data).json()
        except:
            print('load_post error')
        else:
            response_li = response['rows']
            for ret_dict in response_li:
                if not self.rq.in_rset(ret_dict):
                    self.rq.add_to_rset(ret_dict)
                    self.rq.pull_to_rlist(ret_dict)

    def load_get_html(self,ret_dict):
        if ret_dict == None:
            return
        try:
            ret = eval(ret_dict)
            url = 'http://gzg2b.gzfinance.gov.cn/gzgpimp/portalsys/portal.do?method=pubinfoView&&info_id='+ret['info_id']+'&t_k=null'
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:'.format(e))
        else:
            _id = self.hash_to_md5(url)
            title = ret['title']
            status = ret['info_key']
            publish_date = ret['finish_day']
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='row').div
            # print(content_html)

            source = 'http://gzg2b.gzfinance.gov.cn/'
            area_name =self.get_area('广州', title)

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
            retult_dict['zh_name'] = '广州市政府采购平台 '
            retult_dict['en_name'] = 'Guangzhou Government Procurement Platform'

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
            # {'all_page': 329},
            {'all_page': 5},
                   ]
        for task in task_li:
            for page in range(1,task['all_page'] + 1):
                data = [
                    ('current', str(page)),
                    ('rowCount', '10'),
                    ('searchPhrase', ''),
                    ('title_name', ''),
                    ('porid', 'zbcggg'),
                    ('kwd', ''),
                ]

                self.load_get(data)
                print('第{}页'.format(page))

        if self.rq.r_len() >0 :
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
