
import gevent
from gevent import monkey; monkey.patch_all()
import pymongo
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
from utils.encode_code import EncodeStr
import os
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''河北-政府采购网'''
    def __init__(self):
        name = 'hebei_ccgp-hebei_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'If-None-Match': '594gpnM6qpxwGpEvFYoNJpzY8YE=',
            'If-Modified-Since': 'Mon, 23 Jul 2018 02:32:18 GMT',
            'Referer': 'http://www.ccgp-hebei.gov.cn/province/cggg/zhbgg/index_3.html',
            'X-DevTools-Emulate-Network-Conditions-Client-Id': 'F24524FAD50B25DB7D7D89DBCEA53767',
            'Intervention': '<https://www.chromestatus.com/feature/5718547946799104>; level=warning',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='hebei_list1', dbset='hebei_set1')



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
            response = self.session.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:

            title = selector.xpath('//span[@class="txt2"]/text()')
            if title != []:
                title = title[0]
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'


            publish_date = selector.xpath('//body/table/tr/td/table/tr[4]/td/table/tr[7]/td/span/text()')
            # print(publish_date)
            if publish_date !=[]:
                publish_date = re.sub(r'\r|\n|\s|发布时间：','',publish_date[0])
            else:
                publish_date = None
            soup = BeautifulSoup(response)
            content_html = soup.find('body').table.tr.td.table
            # print(content_html)
            area_name = self.get_area('河北',title)
            source = 'http://www.ccgp-hebei.gov.cn/province/'


            _id = self.hash_to_md5(url)

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
            retult_dict['zh_name'] = '河北省政府采购网'
            retult_dict['en_name'] = 'Hebei Province Government Procurement'

            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, params):
        try:
            url = 'http://search.hebcz.gov.cn:8080/was5/web/search'
            response = self.session.get(url=url, headers=self.headers, params=params).text
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
        else:
            url_li = selector.xpath('//tr[@id="biaoti"]/td[2]/a/@href')
            for url in url_li:
                # self.load_get_html(url)
                if not self.rq.in_rset(url):
                    self.rq.add_to_rset(url)
                    self.rq.pull_to_rlist(url)


    def init(self):
        count = 1
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 10
            try:
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        threading.Thread(target=self.init).start()
        #     city_id_li = [
        #         '130100000','130181000','130200000','130300000','130400000','130500000',
        #         '130600000','130682000','130700000','130800000','130900000','131000000','131100000',
        #         '139900000']
        count = 2
        task_li = [
                {'lanmu':'zhbgg','code':130000000,'all_page': count},
                {'lanmu':'zbgg','code':130000000,'all_page': count},
                {'lanmu':'zhbgg','code':130181000,'all_page': count},
                {'lanmu':'zbgg','code':130181000,'all_page': count},
                {'lanmu':'zhbgg','code':130200000,'all_page': count},
                {'lanmu':'zbgg','code':130200000,'all_page': count},
                {'lanmu':'zhbgg','code':130300000,'all_page': count},
                {'lanmu':'zbgg','code':130300000,'all_page': count},
                {'lanmu':'zhbgg','code':130400000,'all_page': count},
                {'lanmu':'zbgg','code':130400000,'all_page': count},
                {'lanmu':'zhbgg','code':130500000,'all_page': count},
                {'lanmu':'zbgg','code':130500000,'all_page': count},
                {'lanmu':'zhbgg','code':130600000,'all_page': count},
                {'lanmu':'zbgg','code':130600000,'all_page': count},
                {'lanmu':'zhbgg','code':130682000,'all_page': count},
                {'lanmu':'zbgg','code':130682000,'all_page': count},
                {'lanmu':'zhbgg','code':130700000,'all_page': count},
                {'lanmu':'zbgg','code':130700000,'all_page': count},
                {'lanmu':'zhbgg','code':130800000,'all_page': count},
                {'lanmu':'zbgg','code':130800000,'all_page': count},
                {'lanmu':'zhbgg','code':130900000,'all_page': count},
                {'lanmu':'zbgg','code':130900000,'all_page': count},
                {'lanmu':'zhbgg','code':131000000,'all_page': count},
                {'lanmu':'zbgg','code':131000000,'all_page': count},
                {'lanmu':'zhbgg','code':131100000,'all_page': count},
                {'lanmu':'zbgg','code':131100000,'all_page': count},
                {'lanmu':'zhbgg','code':139900000,'all_page': count},
                {'lanmu':'zbgg','code':139900000,'all_page': count},
            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                params = {
                    'page': str(page),
                    'channelid':'228483',
                    'perpage':'50',
                    'outlinepage':'10',
                    'lanmu': task['lanmu'],
                    'admindivcode': task['code'],
                    }

                try:
                    self.load_get(params)

                    # spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    # gevent.joinall(spawns)
                except Exception as e:
                    print(e)
                print('第{}页'.format(page))
        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()

