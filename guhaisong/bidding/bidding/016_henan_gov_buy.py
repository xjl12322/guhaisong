import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
import threading
import datetime
import hashlib
import pymongo
from utils.zb_storage_setting import StorageSetting
from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
from utils.cpca import *

class GovBuy(object):
    '''河南政府采购网'''
    def __init__(self):
        name = 'henan_hngp_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.cookies = {
            'sId': '7c61a3bff6dc4969a336157b5f3dfb1d',
        }

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.hngp.gov.cn/henan/search?appCode=H60&pageSize=16&keyword=&dljg=&cgr=&year=2015&pageNo=15',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)

        self.rq = Rdis_Queue(host='localhost', dblist='henan_list1', dbset='henan_set1')

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
        if url == None:
            return
        try:
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            urls_li = re.findall(r'get\(\"(.*?\.htm)\"',response)
            if len(urls_li) < 1:
                return
            urls = 'http://www.hngp.gov.cn'+urls_li[0]
            # print(url)
            response1 = requests.get(url=urls, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:'.format(e))
        else:
            title = selector.xpath('//*[@id="ng-app"]/body/div[3]/div[1]/h1/text()')
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

            publish_date = selector.xpath('//*[@id="ng-app"]/body/div[3]/div[1]/div[1]/span//text()')

            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            content_html = response1.lower()
            if len(content_html) < 100:
                return
            area_name = self.get_area('河南', title)

            source = 'http://www.hngp.gov.cn'

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
            retult_dict['zh_name'] = '河南省政府采购网 '
            retult_dict['en_name'] = 'Henan Province Government Procurement'

            print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            params = {
                'appCode':'H60',
                'pageSize': 10,
                'keyword': '',
                'dljg': '',
                'cgr': '',
                'year': '2019',
                'pageNo': page,
            }

            url = 'http://www.hngp.gov.cn/henan/search'
            response = requests.get(url=url, headers=self.headers,params=params,cookies=self.cookies)
            selector = etree.HTML(response.content.decode('utf-8'))
            url_li = selector.xpath('//div[@class="List2"]/ul/li/a/@href')
            # print(response.url)
            self.headers['Referer'] =response.url
        except:
            print('load_post error')
        else:
            print('第{}页'.format(page))
            # print(url_li)
            # return
            for url in url_li:
                url = 'http://www.hngp.gov.cn'+url
                # print(url)
                self.load_get_html(url)
                if not self.rq.in_rset(url):
                    self.rq.add_to_rset(url)
                    self.rq.pull_to_rlist(url)

    def init(self):
        count = 5
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
                #{'all_page': 500},
                {'all_page': 3},
            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
