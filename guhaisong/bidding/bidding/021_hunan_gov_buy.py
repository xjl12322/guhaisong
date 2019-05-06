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
from utils.zb_storage_setting import StorageSetting


class GovBuy(object):
    '''湖南政府采购网'''
    def __init__(self):
        name = 'hunan_ccgp-hunan_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'http://www.ccgp-hunan.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://www.ccgp-hunan.gov.cn/page/notice/more.jsp?noticeTypeID=prcmNotices',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='hunan_list1', dbset='hunan_set1')

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

    def load_get_html(self,data_dict):
        try:
            url = 'http://www.ccgp-hunan.gov.cn/mvc/viewNoticeContent.do?noticeId=' + str(data_dict['NOTICE_ID'])
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title =data_dict['NOTICE_TITLE']
            # print(title)
            status = data_dict['NOTICE_NAME']

            # print(status)

            _id = self.hash_to_md5(url)

            publish_date = data_dict['NEWWORK_DATE']

            # print(publish_date)
            # area_name = self.get_area('武汉', ''.join(publish_date_li))
            area_name = '湖南'
            source = 'http://www.ccgp-hunan.gov.cn/'

            soup = BeautifulSoup(response)
            content_html = soup.find('table')

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
            retult_dict['zh_name'] = '湖南政府采购网'
            retult_dict['en_name'] = 'Hunan Government Procurement'

            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            data = [
                ('pType', ''),
                ('prcmPrjName', ''),
                ('prcmItemCode', ''),
                ('prcmOrgName', ''),
                ('startDate', '2019-01-17'),
                ('endDate', '2019-12-31'),
                ('prcmPlanNo', ''),
                ('page', page),
                ('pageSize', '18'),
            ]
            url = 'http://www.ccgp-hunan.gov.cn/mvc/getNoticeList4Web.do'
            response = requests.post(url=url, headers=self.headers,data=data).json()
        except:
            print('load_post error')
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            response_li = response['rows']
            # print(response_li)
            for data_dict in response_li:
                print(data_dict)
                self.load_get_html(data_dict)
                # if not self.rq.in_rset(urls):
                #     self.rq.add_to_rset(urls)
                #     self.rq.pull_to_rlist(urls)

    def init(self):
        count = 8
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            try:
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        # threading.Thread(target=self.init).start()
        task_li = [
                # {'all_page': 1000},
                {'all_page': 3},

            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # url =task['url']+str(page)+'.html'
                    # self.load_get(page)
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
