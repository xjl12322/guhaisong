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
from utils.cpca import *
# from utils.proxy_pool import ProxyQueue


class GovBuy(object):
    '''安徽政府采购网'''
    def __init__(self):
        name = 'anhui_ahzfcg_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html, */*; q=0.01',
            'Referer': 'http://www.ahzfcg.gov.cn/',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }

        # self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='anhui_list1', dbset='anhui_set1')

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
            # proxies = self.proxy_queue.get()
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            self.load_get_html(url)
        else:
            title = selector.xpath('//div[@class="frameNews"]/h1/text()')
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

            publish_date = selector.xpath('//div[@class="source"]/span[1]/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            area_name = self.get_area('安徽', title)
            # print(area_name)

            source = 'http://www.ahzfcg.gov.cn/'

            table_ele  = selector.xpath('//div[@class="frameNews"]')[0]

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
            retult_dict['zh_name'] = '安徽省政府采购网'
            retult_dict['en_name'] = 'Anhui Province Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            params = (
                ('pageNum', page),
                ('numPerPage', '20'),
                ('title', ''),
                ('buyer_name', ''),
                ('agent_name', ''),
                ('proj_code', ''),
                ('bid_type', ''),
                ('type', ''),
                ('dist_code', '340000'),
                ('pubDateStart', ''),
                ('pubDateEnd', ''),
                ('pProviceCode', '340000'),
                ('areacode_city', ''),
                ('areacode_dist', ''),
                ('channelCode', 'sjcg_cggg'),
            )
            url = 'http://www.ahzfcg.gov.cn/cmsNewsController/getCgggNewsList.do'
            # proxies = self.proxy_queue.get()
            response = requests.post(url=url, headers=self.headers, params=params).text
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            url_li = selector.xpath('//div[@class="zc_content1"]/div[3]/table/tr/td[1]/a/@href')
            # print(url_li)
            for url in url_li:
                urls = 'http://www.ahzfcg.gov.cn/' + url

                self.load_get_html(urls)
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
                # {'all_page': 21580},
                {'all_page': 3},
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
