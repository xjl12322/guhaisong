import gevent
from gevent import monkey
monkey.patch_all()
from lxml import etree
import time
import datetime
import hashlib
import pymongo

import requests
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting
import json

class GovBuy(object):
    '''南宁公共资源交易信息网'''
    def __init__(self):
        name = 'nanning_nnggzy_net'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.cookies = {
            'yunsuo_session_verify': '2c0b046605eb7acf81b64a462d5a88e3',
            'ASP.NET_SessionId': 'k2oz1d45keci5055fe5br43f',
            '_gscu_1349052524': '33974463sf7nus87',
            '_gscbrs_1349052524': '1',
            '_gscs_1349052524': '3397446376zl7787^|pv:1',
            '__CSRFCOOKIE': 'e0612cbd-55e6-4892-9a1a-bad08d9eafed',
        }

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.nnggzy.net',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.nnggzy.net/nnzbwmanger/ShowInfo/more.aspx?categoryNum=001001001',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        # self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='nanning_nnggzy_net_list1', dbset='nanning_nnggzy_net_set1')

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

    def load_get_html(self, url):
        if url == None:
            return
        try:
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # print(url)
            # self.load_get_html(url)
        else:
            # print(url)
            title = selector.xpath('//span[@id="lblTitle"]//text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',''.join(title))
                try:
                    status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)
            publish_date = selector.xpath('//td[@id="tdTitle"]/font[2]//text()')
            if publish_date != []:
                # publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
                publish_date = re.sub(r'\/','-',re.search(r'(\d{8}|\d{4}\/\d+\/\d{1,2})',''.join(publish_date)).group())
                # if '-' not in publish_date:
                #     publish_date = '{}-{}-{}'.format(publish_date[0:4],publish_date[4:6], publish_date[6:8])
            else:
                publish_date = None
            # print(publish_date, title)
            area_name = '广西-南宁'
            # area_name = '浙江-杭州'
            # print(area_name)

            source = 'http://www.nnggzy.net/'
            # print(url)
            # print(response)

            table_ele  = selector.xpath('//table[@id="tblInfo"]')
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
            retult_dict['zh_name'] = '南宁公共资源交易中心'
            retult_dict['en_name'] = 'Nanning Public resource'
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        try:
            params = (
                ('categoryNum', types),
            )
            data = {
                '__CSRFTOKEN': '/wEFJGUwNjEyY2JkLTU1ZTYtNDg5Mi05YTFhLWJhZDA4ZDllYWZlZA==',
                '__VIEWSTATE': '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',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                '__EVENTARGUMENT': str(page),
                '__VIEWSTATEENCRYPTED': '',
            }
            url = 'http://www.nnggzy.net/nnzbwmanger/ShowInfo/more.aspx'
            response = requests.post(url=url, headers=self.headers, data=data, params=params, cookies=self.cookies).text
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            # time.sleep(3)
            # self.load_get(categoryId, types, page)
        else:
            print('第{}页'.format(page))

            # div_ele_li = selector.xpath('//ul[@class="ewb-right-item"]/li')
            url_li = selector.xpath('//td[@id="MoreInfoList1_tdcontent"]//a/@href')

            # for div_ele in div_ele_li:

            for url in url_li:
                urls = 'http://www.nnggzy.net' + url
                # print(urls)

            # for data_dic in response_li:
                # div = etree.tostring(div_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

                # print(data_dic)
                # self.load_get_html(urls)

                if not self.rq.in_rset(urls):
                    self.rq.add_to_rset(urls)
                    self.rq.pull_to_rlist(urls)

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
                {'categoryId':'', 'types':'001001001','all_page': 1},
                {'categoryId':'', 'types':'001001002','all_page': 2},
                {'categoryId':'', 'types':'001001004','all_page': 1},
                {'categoryId':'', 'types':'001001005','all_page': 2},
                {'categoryId':'', 'types':'001001006','all_page': 1},
                {'categoryId':'', 'types':'001004001','all_page': 2},
                {'categoryId':'', 'types':'001004002','all_page': 1},
                {'categoryId':'', 'types':'001004004','all_page': 2},
                {'categoryId':'', 'types':'001010001','all_page': 1},
            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    categoryId = task['categoryId']
                    types = task['types']

                    # self.load_get(categoryId, page)

                    spawns = [gevent.spawn(self.load_get, categoryId, types, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 10:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
