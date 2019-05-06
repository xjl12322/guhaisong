import requests
from lxml import etree
import threading
import datetime
import hashlib
import pymongo
import gevent
from utils.redis_tool import Rdis_Queue
import re
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting


class GovBuy(object):
    def __init__(self):
        name = 'tianjin_city_gov_buy'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://www.tjgp.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Referer': 'http://www.tjgp.gov.cn/portal/topicView.do?method=view^&view=Infor^&id=1665^&ver=2^&st=1^&stmp=1532324224291',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }

        self.rq = Rdis_Queue(host='localhost', dblist='tianjin_list1', dbset='tianjin_set1')

    def is_running(self):
        is_runing = True
        # if self._post_ret_url_queue.empty() and len (self._post_ret_url_set) > 0:
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


    def load_post(self,data):
        try:
            response = requests.post('http://www.tjgp.gov.cn/portal/topicView.do', headers=self.headers, data=data).content.decode('utf-8')
            selector = etree.HTML(response)
        except:
            print('load_post error')
        else:
            url_li = selector.xpath('//*[@id="reflshPage"]/ul/li/a/@href')
            if url_li != []:
                for url in url_li:
                    url ='http://www.tjgp.gov.cn' + url
                    if not self.rq.in_rset(url):
                        self.rq.add_to_rset(url)
                        self.rq.pull_to_rlist(url)

    def load_get_html(self,url):
        try:
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except:
            print('laod_get_html error')
        else:

            _id = self.hash_to_md5(url)
            # print(_id)
            title = selector.xpath('//body/table/tbody/tr/td/div/p[1]/font/b/text()')
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
            publish_date = selector.xpath('//body/table/tbody/tr/td/div/p[3]/text()')
            if publish_date != []:
                publish_date = publish_date[0]
            else:
                publish_date = None
            # print(publish_date)
            source = 'http://www.tjgp.gov.cn/'
            area_name = self.get_area('',title)

            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['publish_date'] = publish_date
            retult_dict['source'] = source
            retult_dict['area_name'] = area_name
            # #
            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(response)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '天津市政府采购网'
            retult_dict['en_name'] = 'Tianjin government Procurement'

            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))

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
        count = 5
        task_li = [
            {'id':'1665','end_page':count},
            {'id':'1664','end_page':count},
            {'id':'1664','end_page':count},
            {'id':'1666','end_page':count},
            {'id':'2013','end_page':count},
            {'id':'2014','end_page':count},
            {'id':'2015','end_page':count},
            {'id':'2016','end_page':count},
        ]
        for task in task_li:
            for page in range(1,task['end_page'] + 1):
                data = [
                    ('method', 'view'),
                    ('page', str(page)),
                    ('id', task['id']),
                    ('step', '1'),
                    ('view', 'Infor'),
                    ('st', '1'),
                    ('ldateQGE', ''),
                    ('ldateQLE', ''),
                ]
                self.load_post(data)
                print('第{}页'.format(page))

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
