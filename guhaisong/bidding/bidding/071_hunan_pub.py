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
    '''湖南公共资源交易信息网'''
    def __init__(self):
        name = 'hunan_hncg_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.rq = Rdis_Queue(host='localhost', dblist='hunan_hncg_gov_cn_list1', dbset='hunan_hncg_gov_cn_set1')

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

    def load_get_html(self, data_dic):
        if data_dic == None:
            return
        try:
            # selector_div = etree.HTML(str(div))
            url = 'http://www.hncg.gov.cn/portal/protalAction!viewNoticeContent.action?noticeId={}'.format(data_dic['NOTICE_ID'])

            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # print(url)
            # self.load_get_html(url)
        else:
            # print(url)
            # title = selector.xpath('//div[@class="title"]/h2/text()')
            # if title != []:
            #     title = re.sub(r'\r|\n|\s','',''.join(title))
            #     try:
            #         status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
            #     except:
            #         status = '公告'
            # else:
            #     title = None
            #     status = '公告'
            title = data_dic['NOTICE_TITLE']
            status = data_dic['PRCM_MODE_NAME']
            _id = self.hash_to_md5(url)
            publish_date = data_dic['NEWWORK_DATE']
            # publish_date = selector.xpath('//div[@class="title"]/h3//text()')
            # if publish_date != []:
            #     publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            #     # publish_date = re.sub(r'\/','-',re.search(r'(\d{8}|\d{4}\/\d+\/\d{1,2})',''.join(publish_date)).group())
            #     # if '-' not in publish_date:
            #     #     publish_date = '{}-{}-{}'.format(publish_date[0:4],publish_date[4:6], publish_date[6:8])
            # else:
            #     publish_date = None
            print(publish_date, title)
            area_name = '湖南'
            # area_name = '浙江-杭州'
            # print(area_name)

            source = 'http://www.hncg.gov.cn/'
            # print(url)
            # print(response)

            table_ele  = selector.xpath('//html')
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
            retult_dict['zh_name'] = '湖南省公共资源交易中心'
            retult_dict['en_name'] = 'Hunan Province Public resource'
            print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        try:
            params = {
                'title': '',
                'origin': '',
                'inDates': '1',
                'channelId': '845',
                'ext': '',
                'beginTime': '',
                'endTime': '',
            }
            url = 'http://www.hnsggzy.com/queryContent_{}-jygk.jspx'.format(page)
            response = requests.get(url=url, headers=self.headers, params=params).text
            print(response)
            # selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            # time.sleep(3)
            # self.load_get(categoryId, types, page)
        else:
            print('第{}页'.format(page))
            # div_ele_li = selector.xpath('//ul[@class="ewb-right-item"]/li')
            # url_li = selector.xpath('//ul[@id="list_ul"]/li/a/@href')
            # for div_ele in div_ele_li:
            # for url in url_li:
            response_li = response
            for data_dic in response_li:
                # div = etree.tostring(div_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

                print(data_dic)
                # self.load_get_html(data_dic)

    def init(self):
        count = 6
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
                {'categoryId':'', 'types':'','all_page': 2},
                # {'categoryId':'', 'types':'','all_page': 1000},
            ]
        count = 2
        for task in task_li:
            for page in range(0, task['all_page'] + 1, count):
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
