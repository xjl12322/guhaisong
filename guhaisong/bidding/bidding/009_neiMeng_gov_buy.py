
import gevent
from gevent import monkey;monkey.patch_all()
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
from utils.cpca import *
import time
from utils.zb_storage_setting import StorageSetting


class GovBuy(object):
    '''内蒙政府采购网'''
    def __init__(self):
        name = 'neimeng_nmgp_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://www.nmgp.gov.cn/wp-content/themes/caigou_pcweb/skin/css/css.css?ver=2.0',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }


        self.rq = Rdis_Queue(host='localhost', dblist='neimeng_list1', dbset='neimeng_set1')



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
            url = 'http://www.nmgp.gov.cn/zfcgwslave/web/index.php'
            response = requests.get(url=url, headers=self.headers,params=params).json()
        except:
            print('load_post error')
        else:
            if len(response) >= 1:
                response_li = response[0]
            else:
                return
            for ret_dict in response_li:
                if not self.rq.in_rset(ret_dict):
                    self.rq.add_to_rset(ret_dict)
                    self.rq.pull_to_rlist(ret_dict)

    def load_get_html(self,ret_dict):
        # print(ret_dict)
        if ret_dict == None:
            return
        try:
            ret = eval(ret_dict)
            url = 'http://www.nmgp.gov.cn/ay_post/post.php?tb_id=' + ret['ay_table_tag'] + '&p_id=' + ret['wp_mark_id']

            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:'.format(e))
        else:
            # print(ret)
            _id = self.hash_to_md5(url)
            title = ret['TITLE_ALL']
            try:
                status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
            except:
                status = '公告'

            # print(title)
            publish_date = selector.xpath('//*[@id="info-box"]/span/text()')
            if publish_date != []:
                publish_date = re.search(r'\d+年\d+月\d+日',publish_date[0]).group()
            else:
                publish_date = None
            # print(publish_date)
            # return
            end_date = ret['ENDDATE']
            soup = BeautifulSoup(response)
            content_html = soup.find(id='s-main-2').div.div
            # print(content_html)
            # print(content)
            source = 'http://www.nmgp.gov.cn/'
            area_name = self.get_area('内蒙古', title)

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
            retult_dict['zh_name'] = '内蒙古自治区政府采购网 '
            retult_dict['en_name'] = 'NeiMengGu District Government Procurement'

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
            # {'type_name':1, 'all_page': 5268},
            # {'type_name':2, 'all_page': 735},
            # {'type_name':3, 'all_page': 4482},
            # {'type_name':4, 'all_page': 101},
            # {'type_name':5, 'all_page': 925},
            # {'type_name':6, 'all_page': 2386},
            # {'type_name':7, 'all_page': 101},
            # {'type_name':8, 'all_page': 25},
            {'type_name':1, 'all_page': 2},
            {'type_name':2, 'all_page': 2},
            {'type_name':3, 'all_page': 2},
            {'type_name':4, 'all_page': 2},
            {'type_name':5, 'all_page': 2},
            {'type_name':6, 'all_page': 2},
            {'type_name':7, 'all_page': 2},
            {'type_name':8, 'all_page': 1},
                   ]
        for task in task_li:
            for page in range(1,task['all_page'] + 1):
                params = {
                    'r': 'zfcgw/anndata',
                    'type_name': task['type_name'],
                    'byf_page': str(page),
                    'fun': 'cggg',
                }
                if self.rq.r_len() > 8000:
                    time.sleep(3)
                self.load_get(params)
                print('第{}页'.format(page))

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()


    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
