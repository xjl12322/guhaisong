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
    '''江苏政府采购网'''
    def __init__(self):
        name = 'jiangsu_ccgp-jiangsu_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/index_1.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='jiangsu_list1', dbset='jiangsu_set1')

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
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector.xpath('//div[@class="dtit"]/h1/text()')
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

            publish_date = selector.xpath('//div[@class="detail_bz"]/span/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            area_name = self.get_area('江苏', title)
            # print(area_name)

            source = 'http://www.ccgp-jiangsu.gov.cn/'

            table = selector.xpath('//div[@class="detail"]')
            if table != []:
                table = table[0]
            else:
                return
            content_html = etree.tostring(table, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

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
            retult_dict['zh_name'] = '江苏政府采购网'
            retult_dict['en_name'] = 'Jiangsu Government Procurement'
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, base_url, page):
        try:
            if page == 0:
                url = base_url
            else:
                url = base_url + 'index_' + str(page) + '.html'
            response = requests.get(url=url, headers=self.headers ).content.decode('utf-8')
            selector = etree.HTML(response)
        except:
            print('load_post error')
            # self.load_get(url)
        else:
            # print('第{}页'.format(page))
            url_li = selector.xpath('//div[@class="list_list"]/ul/li/a/@href')
            if url_li == []:
                url_li = selector.xpath('//div[@class="list_list02"]/ul/li/a/@href')

            for url in url_li:
                urls = base_url + url.replace('./','')
                # print(urls)
                # self.load_get_html((urls))
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
        flag = 2
        task_li = [
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cgyg/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/htgg/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/xqyj/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/ysgg/', 'all_page': flag},

                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/shengji/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/suzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/nanjing/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/wuxi/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/changzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/zhenjiang/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/nantong/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/yangzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/yancheng/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/huaian/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/suqian/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/lianyungang/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/xuzhou/', 'all_page': flag},

                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/shengji/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/suzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/nanjing/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/wuxi/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/changzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/zhenjiang/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/nantong/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/taizhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/yangzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/yancheng/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/huaian/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/suqian/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/lianyungang/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/xuzhou/', 'all_page': flag},

                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/shengji/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/suzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/nanjing/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/wuxi/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/changzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/zhenjiang/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/nantong/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/taizhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/yangzhou/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/yancheng/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/huaian/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/suqian/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/lianyungang/', 'all_page': flag},
                {'url':'http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/xuzhou/', 'all_page': flag},
            ]
        count = 3
        for task in task_li:
            for page in range(0, task['all_page'] + 1 , count):
                try:
                    base_url = task['url']

                    # self.load_get(base_url, page)
                    spawns = [gevent.spawn(self.load_get,base_url,  page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
