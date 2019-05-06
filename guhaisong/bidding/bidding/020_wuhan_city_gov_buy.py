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
    '''武汉政府采购网'''
    def __init__(self):
        name = 'wuhan_cgb_wuhan_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://cgb.wuhan.gov.cn/notice/zbgg//index_2.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='wuhan_list1', dbset='wuhan_set1')

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

    def load_get_html(self,li):
        try:
            selector_li = etree.HTML(str(li))
            url = 'http://cgb.wuhan.gov.cn'+selector_li.xpath('//li/a/@href')[0]

            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector_li.xpath('//li/a/text()')
            if title != []:
                title = title[0]
            else:
                title = None
            # print(title)
            status = selector_li.xpath('//li/div/span[3]/font/text()')
            if status != []:
                status = str(status[0])
            else:
                status = None

            _id = self.hash_to_md5(url)

            publish_date_li = selector_li.xpath('//li/span/text()')

            if publish_date_li != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date_li)).group()
            else:
                publish_date = None
            # print(publish_date)
            # area_name = self.get_area('武汉', ''.join(publish_date_li))
            area_name = '武汉'
            source = 'http://cgb.wuhan.gov.cn/'

            soup = BeautifulSoup(response)
            content_html = soup.find(class_='art_con')

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
            retult_dict['zh_name'] = '武汉政府采购网'
            retult_dict['en_name'] = 'Wuhan Government Procurement'

            print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, url):
        try:
            response = requests.post(url=url, headers=self.headers).content.decode('utf-8')
            print(response)
            soup = BeautifulSoup(response)
        except:
            print('load_post error')
            self.load_get(url)
        else:
            ul = soup.find(class_="news-list-content list-unstyled")
            ul_li = ul.find_all('li')
            for li in ul_li:
                self.load_get_html(li)
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
                {'url':'http://cgb.wuhan.gov.cn/notice/zbgg//index_', 'all_page': 3},
                {'url': 'http://cgb.wuhan.gov.cn/notice/cggg/index_', 'all_page': 3},
                {'url': 'http://cgb.wuhan.gov.cn/notice/gzgg/index_', 'all_page': 3},
                {'url': 'http://cgb.wuhan.gov.cn/notice/fbgg/index_', 'all_page': 3},
                {'url': 'http://cgb.wuhan.gov.cn/notice/dylygg/index_', 'all_page': 2},
                {'url': 'http://cgb.wuhan.gov.cn/notice/qtgg/index_', 'all_page': 2},
                {'url': 'http://cgb.wuhan.gov.cn/notice/jkcpgg/index_', 'all_page': 1},
                {'url': 'http://cgb.wuhan.gov.cn/notice/dzscgg/index_', 'all_page': 2},
                {'url': 'http://cgb.wuhan.gov.cn/contract/index_', 'all_page': 2},
            ]
        count = 3
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # url =task['url']+str(page)+'.html'
                    # self.load_get(url)
                    spawns = [gevent.spawn(self.load_get, task['url']+str(page + i)+'.html') for i in range(count)]
                    gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
