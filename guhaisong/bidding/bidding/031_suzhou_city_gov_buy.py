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
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''苏州政府采购网'''
    def __init__(self):
        name = 'suzhou_zfcg_suzhou_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://www.zfcg.suzhou.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://www.zfcg.suzhou.gov.cn/html/search.shtml?title=&choose=&projectType=0&zbCode=&appcode=',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }

        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='suzhou_list1', dbset='suzhou_set1')

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

    def load_get_html(self,pid):
        if pid == None:
            return
        try:
            url = 'http://www.zfcg.suzhou.gov.cn/html/project/'+ pid +'.shtml'
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector.xpath('//div[@class="M_title"]/text()')
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

            publish_date = selector.xpath('//div[@class="date"]/span/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            area_name = '江苏-苏州'
            # print(area_name)

            source = 'http://www.zfcg.suzhou.gov.cn/'

            table_ele  = selector.xpath('//div[@id="tab1"]')[0]

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
            retult_dict['zh_name'] = '苏州市政府采购网'
            retult_dict['en_name'] = 'Suzhou City Government Procurement'
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, types, page):
        try:
            data = [
                ('title', ''),
                ('choose', ''),
                ('type', types),
                ('zbCode', ''),
                ('appcode', ''),
                ('page', page),
                ('rows', '30'),
            ]
            url = 'http://www.zfcg.suzhou.gov.cn/content/searchContents.action'
            response = requests.post(url=url, headers=self.headers, data=data).json()
            # selector = etree.HTML(response)
        except:
            print('load_post error')
            self.load_get(types, page)
        else:
            print('第{}页'.format(page))
            # print(response)
            response_li = response['rows']
            if response_li == []:
                return

            for project_id in response_li:
                pid = project_id['PROJECTID']

                # self.load_get_html(pid)
                if not self.rq.in_rset(pid):
                    self.rq.add_to_rset(pid)
                    self.rq.pull_to_rlist(pid)

    def init(self):
        count = 3
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
        task_li = [
                {'type':'0', 'all_page': 2},
                {'type':'1', 'all_page': 2},
                {'type':'2', 'all_page': 2},

            ]
        count = 3
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    types = task['type']

                    # self.load_get(base_url, page)
                    spawns = [gevent.spawn(self.load_get,types, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()


    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
