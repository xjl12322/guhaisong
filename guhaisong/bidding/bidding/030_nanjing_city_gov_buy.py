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
from utils import proxy_pool

class GovBuy(object):
    '''南京政府采购网'''
    def __init__(self):
        name = 'nanjing_njgp_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.njgp.gov.cn/cgxx/cggg/jzcgjg/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='nanjing_list1', dbset='nanjing_set1')

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
        # print(url)
        try:
            proxies = proxy_pool.proxies ()
            response = requests.get(url=url, headers=self.headers, proxies=proxies).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector.xpath('//div[@class="title"]/h1/text()')
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

            publish_date = selector.xpath('//div[@class="extra"]/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            area_name = '江苏-南京'
            # print(area_name)

            source = 'http://www.njgp.gov.cn/'

            table_ele_li = selector.xpath('//div[@class="cont"]/div')
            content_html = ''
            for table_ele in table_ele_li[1:4]:

                content_html += etree.tostring(table_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

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
            retult_dict['zh_name'] = '南京市政府采购网'
            retult_dict['en_name'] = 'Nanjing City Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, base_url, page):
        try:
            if page == 0:
                url = base_url
            else:
                url = base_url + 'index_' + str(page) + '.html'
            proxies = proxy_pool.proxies ()
            response = requests.get(url=url, headers=self.headers, proxies=proxies).content.decode('utf-8')
            selector = etree.HTML(response)
        except:
            print('load_post error')
        else:
            print('第{}页'.format(page))
            url_li = selector.xpath('//div[@class="R_cont_detail"]/ul/li/a/@href')
            for url in url_li:
                urls = base_url + url.replace('./','')
                print(urls)
                self.load_get_html((urls))
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
                {'url':'http://www.njgp.gov.cn/cgxx/cggg/jzcgjg/', 'all_page': 3},
                {'url':'http://www.njgp.gov.cn/cgxx/cggg/bmjzcgjg/', 'all_page': 3},
                {'url':'http://www.njgp.gov.cn/cgxx/cggg/qjcgjg/', 'all_page': 2},
                {'url':'http://www.njgp.gov.cn/cgxx/cggg/shdljg/', 'all_page': 3},
                {'url':'http://www.njgp.gov.cn/cgxx/cggg/qtbx/', 'all_page': 1},
            ]
        count = 3
        for task in task_li:
            for page in range(0, task['all_page'] + 1, count):
                try:
                    base_url = task['url']
                    # self.load_get(base_url, page)
                    spawns = [gevent.spawn(self.load_get,base_url,  page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
