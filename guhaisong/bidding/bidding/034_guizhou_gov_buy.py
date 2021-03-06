import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
import time
import datetime
import hashlib
import pymongo
from utils.zb_storage_setting import StorageSetting
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
# from utils.proxy_pool import ProxyQueue


class GovBuy(object):
    '''贵州政府采购网'''
    def __init__(self):
        name = 'guizhou_ccgp-guizhou_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.cookies = {
            'yunsuo_session_verify': '53d713a24aa824764131cb472ee5682c',
            'JSESSIONID': 'A8C797550A5964C7AF289D93784B1626',
        }

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.ccgp-guizhou.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='guizhou_list1', dbset='guizhou_set1')

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
        if li == None:
            return
        try:
            selector_li = etree.HTML(str(li))
            url = 'http://www.ccgp-guizhou.gov.cn' + selector_li.xpath('//li/a/@href')[0]
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            self.load_get_html(url)
        else:
            title = selector_li.xpath('//li/a/text()')
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

            publish_date = selector_li.xpath('//li/span/text()')
            if publish_date != []:
                publish_date = re.sub(r'\.','-',re.search(r'(\d{4}\.\d+\.\d{1,2})',''.join(publish_date)).group())
            else:
                publish_date = None
            # print(publish_date)
            area_name = self.get_area('贵州', title)
            # print(area_name)

            source = 'http://www.ccgp-guizhou.gov.cn/'

            table_ele  = selector.xpath('//div[@class="you"]')
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
            retult_dict['zh_name'] = '贵州省政府采购网'
            retult_dict['en_name'] = 'Guizhou Province Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            # time.sleep(2)
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            data = [
                ('siteId', '1'),
                ('category.id', ''),
                ('areaName', ''),
                ('tenderRocurementPm', ''),
                ('keywords', ''),
                ('articlePageNo', page),
                ('articlePageSize', '15'),
            ]

            url = 'http://www.ccgp-guizhou.gov.cn/article-search.html'
            # proxies = self.proxy_queue.get()
            response = requests.post(url=url, headers=self.headers, data=data).text
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            li_ele_li = selector.xpath('//div[@class="xnrx"]/ul/li')

            for li_ele in li_ele_li:
                li = etree.tostring(li_ele, pretty_print=True,encoding='utf-8',method='html').decode('utf-8')

                self.load_get_html(li)

                # self.load_get_html(urls)
                # if not self.rq.in_rset(urls):
                #     self.rq.add_to_rset(urls)
                #     self.rq.pull_to_rlist(urls)


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
        # threading.Thread(target=self.init).start()
        task_li = [
                # {'all_page': 8639},
                {'all_page': 2},
            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # self.load_get(base_url, page)
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
