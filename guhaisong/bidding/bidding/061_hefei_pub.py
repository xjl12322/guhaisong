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
from utils.proxy_pool import proxies

class GovBuy(object):
    '''合肥公共资源交易信息网'''
    def __init__(self):
        name = 'hefei_ggzy_hefei_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Host': 'ggzy.hefei.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'Connection': 'close',
            
        }
        
        self.session = requests.session()
        
        self.rq = Rdis_Queue(host='localhost', dblist='hefei_ggzy_hefei_gov_cn_list1', dbset='hefei_ggzy_hefei_gov_cn_set1')

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

    def get_cookies(self):
        url = 'http://ggzy.hefei.gov.cn/jyxx/002001/engineer.html'
        response = self.session.get(url=url,headers=self.headers)
        response = self.session.get(url=url,headers=self.headers)

    def load_get_html(self, div):
        if div == None:
            return
        try:
            selector_div = etree.HTML(str(div))
            url = 'http://ggzy.hefei.gov.cn'+ selector_div.xpath('//li/a/@href')[0]
            print(url)
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # print(url)
            # self.load_get_html(url)
        else:
            title = selector_div.xpath('//li/a/@title')
            if title != []:
                title = re.sub(r'\r|\n|\s','',''.join(title))
                try:
                    status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)

            publish_date = selector_div.xpath('//span/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            else:
                publish_date = None
            print(publish_date, title)
            # area_name = self.get_area()
            area_name = '安徽-合肥'

            source = 'http://ggzy.hefei.gov.cn/'

            table_ele  = selector.xpath('//div[@class="ewb-main"]')
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
            retult_dict['zh_name'] = '合肥市公共资源交易平台'
            retult_dict['en_name'] = 'Hefei City Public resource'
            print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        self.get_cookies()
        try:
            
            if page == 1:
                pages = 'moreinfo_jyxxgg'
            else:
                pages = str(page)
            url = 'http://ggzy.hefei.gov.cn/jyxx/002001/002001001/2.html'
            # url = 'http://ggzy.hefei.gov.cn/jyxx/{}/{}.html'.format(types, pages)
            response = self.session.get(url=url, headers=self.headers).content.decode('utf-8')
            # self.headers['Referer'] = url
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            # time.sleep(3)
            # self.load_get(categoryId, types, page)
        else:
            print(response)
            print('第{}页'.format(page))
            div_ele_li = selector.xpath('//ul[@class="ewb-right-item"]/li')

            for div_ele in div_ele_li:
                div = etree.tostring(div_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
                # self.load_get_html(div)
                print(div)
                # if not self.rq.in_rset(pid):
                #     self.rq.add_to_rset(pid)
                #     self.rq.pull_to_rlist(pid)

    def run(self):
        task_li = [
                {'categoryId':'', 'types':'002001/002001001','all_page': 2},
                # {'categoryId':'', 'types':'002001/002001002','all_page': 2},
                # {'categoryId':'', 'types':'002001/002001003','all_page': 2},
                # {'categoryId':'', 'types':'002001/002001004','all_page': 2},
                # {'categoryId':'', 'types':'002001/002001005','all_page': 2},
                # {'categoryId':'', 'types':'002002/002002001','all_page': 2},
                # {'categoryId':'', 'types':'002002/002002002','all_page': 2},
                # {'categoryId':'', 'types':'002002/002002003','all_page': 3},
                # {'categoryId':'', 'types':'002002/002002004','all_page': 1},
                # {'categoryId':'', 'types':'002002/002002005','all_page': 1},
                # {'categoryId':'', 'types':'002003/002003001','all_page': 1},
                # {'categoryId':'', 'types':'002003/002003002','all_page': 1},
                # {'categoryId':'', 'types':'002003/002003003','all_page': 1},
                # {'categoryId':'', 'types':'002003/002003004','all_page': 1},
                # {'categoryId':'', 'types':'002003/002003005','all_page': 1},
                # {'categoryId':'', 'types':'002004/002004001','all_page': 1},
                # {'categoryId':'', 'types':'002004/002004002','all_page': 1},
                # {'categoryId':'', 'types':'002004/002004003','all_page': 1},
            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
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
