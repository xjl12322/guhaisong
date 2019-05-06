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

class GovBuy(object):
    '''云南政府采购网'''
    def __init__(self):
        name = 'yunnan_yngp_com'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://www.yngp.com',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Referer': 'http://www.yngp.com/bulletin.do?method=moreList',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }

        self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='yunnan_list1', dbset='yunnan_set1')

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

    def load_get_html(self, data_dict):
        if data_dict == None:
            return
        try:
            bid = data_dict['bulletin_id']
            url = 'http://www.yngp.com/newbulletin_zz.do?method=preinsertgomodify&operator_state=1&flag=view&bulletin_id='+bid
            response = requests.get(url=url, headers=self.headers).content.decode("gb18030")
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # self.load_get_html(li)
        else:
            # title = selector.xpath('//h1[@class="content-tit"]/text()')
            title = data_dict['bulletintitle']
            # if title != []:
                # title = re.sub(r'\r|\n|\s','',title[0])
            try:
                status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
            except:
                status = '公告'
            # else:
            #     title = None
            #     status = '公告'
            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            # publish_date = selector.xpath('//div[@class="content_about"]/span[2]/em/text()')
            publish_date = data_dict['finishday']
            # if publish_date != []:
            #     publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            # else:
            #     publish_date = None
            # print(publish_date)
            area_name = self.get_area('云南',data_dict['codeName'])

            # print(area_name)

            source = 'http://www.yngp.com/'

            table_ele  = selector.xpath('//div[@id="searchPanel"]')
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
            retult_dict['zh_name'] = '云南省政府采购网'
            retult_dict['en_name'] = 'Yunnan Province Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)


    def load_get(self,query_sign, page):
        try:
            params = (
                ('method', 'moreListQuery'),
            )
            data = {
                'current': page,
                'rowCount': '10',
                'searchPhrase': '',
                'query_bulletintitle': '',
                'query_startTime': '',
                'query_endTime': '',
                'query_sign': query_sign,
            }
            url = 'http://www.yngp.com/bulletin.do'
            response = requests.post(url=url, headers=self.headers, params=params,data=data).json()

            # selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            # self.load_get(types,page)
        else:
            print('第{}页'.format(page))
            response_li = response['rows']
            for data_dict in response_li:
                # print(data_dict)
                self.load_get_html(data_dict)
                # if not self.rq.in_rset(urls):
                #     self.rq.add_to_rset(urls)
                #     self.rq.pull_to_rlist(urls)

    def init(self):
        count = 1
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
        # threading.Thread(target=self.init).start()
        task_li = [
                {'query_sign':'1', 'all_page': 3},
                {'query_sign':'4', 'all_page': 2},
                {'query_sign':'3', 'all_page': 2},
                {'query_sign':'5', 'all_page': 2},
                {'query_sign':'2', 'all_page': 3},
                {'query_sign':'6', 'all_page': 3},

            ]
        count = 3
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    query_sign = task['query_sign']
                    # self.load_get(types, page)
                    spawns = [gevent.spawn(self.load_get,query_sign, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
