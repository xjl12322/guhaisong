import gevent
from gevent import monkey
monkey.patch_all()
from lxml import etree
import time
import datetime
import hashlib
import pymongo
import gevent
from gevent import monkey
monkey.patch_all()
import requests
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting
import json

class GovBuy(object):
    '''乌鲁木齐公共资源交易信息网'''
    def __init__(self):
        name = 'wulumuqi_ggzy_wlmq_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://ggzy.wlmq.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'text/plain',
            'Accept': '*/*',
            'Referer': 'http://ggzy.wlmq.gov.cn/generalpage.do?method=showList&fileType=201605-048&faname=201605-046',
            'Connection': 'keep-alive',
        }

        # self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='wulumuqi_list1', dbset='wulumuqi_set1')

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

    def load_get_html(self, info_id):
        if info_id == None:
            return
        try:
            url = 'http://ggzy.wlmq.gov.cn/infopublish.do?method=infoPublishView&infoid=' + info_id
            response = requests.get(url=url, headers=self.headers).content.decode('gb18030')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            print(url)
            # self.load_get_html(url)
        else:
            title = selector.xpath('//div[@class="title"]/text()')
            if title != '':
                title = re.sub(r'\r|\n|\s','',title[0])
                try:
                    status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//td[@class="td_name"]//text()')
            if publish_date != []:
                # publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
                publish_date = re.search(r'(\d{8}|\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
                # if '-' not in publish_date:
                #     publish_date = '{}-{}-{}'.format(publish_date[0:4],publish_date[4:6], publish_date[6:8])
            else:
                publish_date = None
            # print(publish_date)
            # area_name = self.get_area('云南',title)
            area_name = '新疆-乌鲁木齐'
            # print(area_name)

            source = 'http://ggzy.wlmq.gov.cn/'

            table_ele  = selector.xpath('//div[@class="w_content_main"]')
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
            retult_dict['zh_name'] = '乌鲁木齐市公共资源交易网'
            retult_dict['en_name'] = 'Urumqi City Public resource'
            
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        try:
            data = 'callCount=1\n\npage=/generalpage.do?method=showList&fileType='+categoryId+'&faname=201605-046\n\nhttpSessionId=\n\nscriptSessionId=A0890501B5665F11F1222EBC440FC5FC644\n\nc0-scriptName=projectDWR\n\nc0-methodName=queryItemInfoByIndustryType2\n\nc0-id=0\n\nc0-e1=string:packTable\n\nc0-e2=string:'+categoryId+'\n\nc0-e3=number:'+str(page)+'\n\nc0-e4=string:15\n\nc0-e5=string:true\n\nc0-e6=string:packTable\n\nc0-e7=string:982\n\nc0-param0=Object_Object:{flag:reference:c0-e1, name:reference:c0-e2, currentPage:reference:c0-e3, pageSize:reference:c0-e4, isPage:reference:c0-e5, tabId:reference:c0-e6, totalRows:reference:c0-e7}\n\nbatchId=3\n\n'
            url = 'http://ggzy.wlmq.gov.cn/dwr/call/plaincall/projectDWR.queryItemInfoByIndustryType2.dwr'
            response = requests.post(url=url, headers=self.headers, data=data).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(categoryId, types, page)
        else:
            print('第{}页'.format(page))
            info_id_il = re.findall(r"""\[\'FILE_ID\'\]\=\"(.*?)\"\;""", response)
            print(info_id_il)
            for pid in info_id_il:
                # print(info_id)
                # self.load_get_html(pid)

                if not self.rq.in_rset(pid):
                    self.rq.add_to_rset(pid)
                    self.rq.pull_to_rlist(pid)
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
        threading.Thread(target=self.init).start()
        task_li = [
                {'categoryId':'201605-048', 'types':'','all_page': 2},
                {'categoryId':'201605-049', 'types':'','all_page': 1},
                {'categoryId':'201605-050', 'types':'','all_page': 2},
                {'categoryId':'201605-051', 'types':'','all_page': 1},
                {'categoryId':'201605-052', 'types':'','all_page': 1},
                {'categoryId':'201605-053', 'types':'','all_page': 1},
                {'categoryId':'201605-039', 'types':'','all_page': 2},
                {'categoryId':'201605-041', 'types':'','all_page': 1},
                {'categoryId':'201605-042', 'types':'','all_page': 1},
                {'categoryId':'201605-043', 'types':'','all_page': 2},
                {'categoryId':'201605-044', 'types':'','all_page': 2},
                {'categoryId':'201605-045', 'types':'','all_page': 2},
            ]
        count = 3
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

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
