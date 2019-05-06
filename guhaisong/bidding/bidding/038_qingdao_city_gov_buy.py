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

class GovBuy(object):
    '''青島政府采购网'''
    def __init__(self):
        name = 'qingdao_ccgp-qingdao_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'https://www.ccgp-qingdao.gov.cn',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'text/plain',
            'Accept': '*/*',
            'Referer': 'https://www.ccgp-qingdao.gov.cn/sdgp2014/site/channelall370200.jsp?colcode=0401^&flag=0401',
            'Connection': 'keep-alive',
        }

        self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='qingdao_list1', dbset='qingdao_set1')

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

    def load_get_html(self, ids):

        if ids == None:
            return
        try:
            url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/site/read370200.jsp?id='+ str(ids)
            # print(url)
            response = requests.get(url=url, headers=self.headers, verify=False).content.decode("gb18030")
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # self.load_get_html(li)
        else:
            title = selector.xpath('//div[@class="biaot"]/text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',title[0])
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'
            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//div[@class="biaotq"]/text()')
            if publish_date != []:
                publish_date = re.sub(r'年|月','-',re.search(r'(\d{4}年\d+月\d{1,2})',''.join(publish_date)).group())
            else:
                publish_date = None
            # print(publish_date)
            area_name = '山东-青島'

            source = 'https://www.ccgp-qingdao.gov.cn/'

            table_ele  = selector.xpath('//div[@class="cont"]')
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
            retult_dict['zh_name'] = '青岛市政府采购网'
            retult_dict['en_name'] = 'Qingdao City Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)


    def load_get(self,types, page):
        try:
            # url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/dwr/call/plaincall/dwrmng.queryWithoutUi.dwr'
            url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/dwr/call/plaincall/dwrmng.queryWithoutUi.dwr'

            data = {
                'callCount': '1',
                'windowName': '',
                'c0-scriptName': 'dwrmng',
                'c0-methodName': 'queryWithoutUi',
                'c0-id': '0',
                'c0-param0': 'number:7',
                'c0-e1': 'string:'+types,
                'c0-e2': 'string:'+str(page),
                'c0-e3': 'number:10',
                'c0-e4': 'string:',
                'c0-e5': 'null:null',
                'c0-param1': 'Object_Object:{_COLCODE:reference:c0-e1, _INDEX:reference:c0-e2, _PAGESIZE:reference:c0-e3, _REGION:reference:c0-e4, _KEYWORD:reference:c0-e5}',
                'batchId': '8',
                'page': '%2Fsdgp2014%2Fsite%2Fchannelall370200.jsp%3Fcolcode%3D0401%26flag%3D0401',
                'httpSessionId': '',
                'scriptSessionId': '9BCA99F81A827529F202FF26A81421A0',
            }
            response = requests.post(url=url, headers=self.headers, data=data, verify=False).text

            a = re.findall(r'rsltStringValue:"(.*?)"',response)[0]
        except Exception as e:
            print('load_get error:{}'.format(e))
            # self.load_get(types,page)
        else:
            print('第{}页'.format(page))
            b = a.split('?')
            for i in b:
                ids = i.split(',')[0]
                self.load_get_html(ids)

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
                {'types':'0401', 'all_page': 3},
                {'types':'0402', 'all_page': 3},
                {'types':'0403', 'all_page': 2},
                {'types':'0404', 'all_page': 2},
                {'types':'0405', 'all_page': 2},
                {'types':'0406', 'all_page': 1},
            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    types = task['types']
                    self.load_get(types, page)
                    spawns = [gevent.spawn(self.load_get,types, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
