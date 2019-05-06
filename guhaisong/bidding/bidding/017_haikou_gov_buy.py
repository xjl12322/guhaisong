import gevent
from gevent import monkey; monkey.patch_all()
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
from utils.encode_code import EncodeStr
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''海口政府采购网'''
    def __init__(self):
        name = 'haikou_ggzy_haikou_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://ggzy.haikou.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://ggzy.haikou.gov.cn/login.do?method=newsecond^&param=431241696e6465783d3326747970653d5a435f4a59',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='haikou_list1', dbset='haikou_set1')

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

    def load_get_html(self,url):
        try:
            if url ==None:
                return
            response = requests.get(url=url, headers=self.headers).text
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector.xpath('//div[@class="part_1"]/div[1]/text()')
            if title != []:
                title = title[0]
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'
            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//div[@class="part_1"]/div[2]//text()')

            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='content_wrap')

            area_name = self.get_area('海口', title)

            source = 'http://ggzy.haikou.gov.cn'

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
            retult_dict['zh_name'] = '海口公共资源交易网'
            retult_dict['en_name'] = 'Hiakou Public resource'

            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, data):
        try:
            params = (
                ('method', 'getSecondTableInfo'),
            )
            url = 'http://ggzy.haikou.gov.cn/login.do'
            response = requests.post(url=url, headers=self.headers, params=params, data=data).json()
        except:
            print('load_post error')
        else:
            response_li = response['result']
            for dic in response_li:
                key_str = 'flag=3&name='+dic['FLAG']+'&key='+dic['KEYID']
                es = EncodeStr(key_str)
                encodestr = es.encodes()
                urls = 'http://ggzy.haikou.gov.cn/login.do?method=newDetail&param='+encodestr
                # print(urls)
                if not self.rq.in_rset(urls):
                    self.rq.add_to_rset(urls)
                    self.rq.pull_to_rlist(urls)

    def init(self):
        count = 6
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
        flag = 3
        task_li = [
                {'type':'GC_JY', 'all_page': flag},
                {'type':'GC_GS', 'all_page': flag},
                {'type':'GC_JG', 'all_page': flag},
                {'type':'ZC_JY', 'all_page': flag},
                {'type':'ZC_JG', 'all_page': flag},
            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                data = [
                    ('currentPage', str(page)),
                    ('pageSize', '20'),
                    ('flag', '3'),
                    ('type', task['type']),
                    ('notice_title', ''),
                ]
                try:
                    self.load_get(data)
                    print('第{}页'.format(page))
                    # spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    # gevent.joinall(spawns)
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()


    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
