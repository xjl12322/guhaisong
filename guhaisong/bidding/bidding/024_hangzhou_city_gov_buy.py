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
    '''杭州政府采购网'''
    def __init__(self):
        name = 'hangzhou_cg_hzft_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Cache-Control': 'max-age=0',
            'Origin': 'http://cg.hzft.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://cg.hzft.gov.cn/www/noticelist.do',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
}

        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='hangzhou_list1', dbset='hangzhou_set1')

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
        try:
            response = requests.get(url=url, headers=self.headers).text
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector.xpath('//div[@class="detail_con"]/h1/text()')
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
            # print(status)
            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//div[@class="content_about"]//text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)

            area_name = '杭州'

            source = 'http://cg.hzft.gov.cn/'

            soup = BeautifulSoup(response)
            content_html = soup.find(class_='detail_con')
            # print(content_html)

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
            retult_dict['zh_name'] = '杭州市政府采购网'
            retult_dict['en_name'] = 'Hangzhou Government Procurement'
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, data):
        try:
            url = 'http://cg.hzft.gov.cn/www/noticelist.do'
            # proxies = self.proxy_queue.get()
            response = requests.post(url=url, headers=self.headers, data=data).text
            selector = etree.HTML(response)
        except:
            print('load_post error')
            self.load_get(data)
        else:
            # print('第{}页'.format(page))
            url_li = selector.xpath('//ul[@class="c_list_item"]/li/a/@href')
            print(url_li)
            for url in url_li:
                urls = 'http://cg.hzft.gov.cn/'+url

                # self.load_get_html(urls)
                if not self.rq.in_rset(urls):
                    self.rq.add_to_rset(urls)
                    self.rq.pull_to_rlist(urls)

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
        threading.Thread(target=self.init).start()
        task_li = [
                {'regionguid': '330100', 'noticetype': '3,3001,3002,3008,3009,3011,3014,4001,4002','all_page': 1},
                {'regionguid': '3', 'noticetype': '5,6','all_page': 1},
                {'regionguid': '', 'noticetype': '1,3012','all_page': 1},
            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                data = {
                    'page.pageNum': page,
                    "parameters['regionguid']": task['regionguid'],
                    "parameters['noticetype']": task['noticetype'],
                    "parameters['title']": ''
                }
                try:
                    self.load_get(data)
                    # spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    # gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()


    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
