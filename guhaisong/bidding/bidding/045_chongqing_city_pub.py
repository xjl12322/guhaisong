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
# from utils.proxy_pool import ProxyQueue
import json

class GovBuy(object):
    '''重庆公共资源交易信息网'''
    def __init__(self):
        name = 'chongqing_cqggzy_com'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Referer': 'https://www.cqggzy.com/xxhz/014001/014001001/zbggjyxx-page.html',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Host':'www.cqggzy.com',
        }

        # self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

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

    def load_get_html(self, data_dic):
        print(data_dic)
        if data_dic == None:
            return
        try:
            url = 'https://www.cqggzy.com'+data_dic['infourl']
            print(url)
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # print(url)
            # self.load_get_html(url)
        else:
            # print(response)
            title = data_dic['title']
            # title = selector.xpath('//div[@class="div-title"]/text()')
            if title != '':
                title = re.sub(r'\r|\n|\s','',title)
                try:
                    status = re.search(r'["招标","预","采购","更正","结果","补充"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)

            # publish_date = selector.xpath('//div[@class="div-title2"]//text()')
            publish_date = data_dic['infodate']
            # if publish_date != []:
            #     publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            # else:
            #     publish_date = None
            area_name = '重庆-' + data_dic['infoC']

            source = 'https://www.cqggzy.com'

            table_ele  = selector.xpath('//div[@class="detail-block"]')
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
            retult_dict['zh_name'] = '重庆市公共资源交易网'
            retult_dict['en_name'] = 'Chongqing City Public resource'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, page):
        try:
            params = {
                'response': 'application/json',
                'pageIndex': page,
                'pageSize': '18',
                'siteguid': 'd7878853-1c74-4913-ab15-1d72b70ff5e7',
                'categorynum': categoryId,
                'title': '',
                'infoC': '',
                '_': str(int(time.time() * 1000)),
            }
            url = 'https://www.cqggzy.com/web/services/PortalsWebservice/getInfoList'
            response = requests.get(url=url, headers=self.headers,params=params, verify=False).json()
            # selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(categoryId, page)
        else:
            print('第{}页'.format(page))
            response_li = json.loads(response['return'])

            for data_dic in response_li:
                self.load_get_html(data_dic)

                # if not self.rq.in_rset(pid):
                #     self.rq.add_to_rset(pid)
                #     self.rq.pull_to_rlist(pid)

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
        # print(os.getppid())
        # threading.Thread(target=self.init).start()
        task_li = [
                {'categoryId':'014001001','all_page': 3},
                {'categoryId':'014001014','all_page': 3},
                {'categoryId':'014001004','all_page': 3},

            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:

                    categoryId = task['categoryId']

                    # self.load_get(categoryId, page)

                    spawns = [gevent.spawn(self.load_get, categoryId, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
