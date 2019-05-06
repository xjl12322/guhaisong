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

class GovBuy(object):
    '''福建政府采购网'''
    def __init__(self,source,base_url, all_page):
        name = 'fujian_cz_fjzfcg_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://cz.fjzfcg.gov.cn/3500/noticelist/d03180adb4de41acbb063875889f9af1/?page=1',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }
        self.session = requests.session()
        self.source = source
        self.base_url = base_url
        self._all_page = all_page


        self.rq = Rdis_Queue(host='localhost', dblist='fujian_list1', dbset='fujian_set1')

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

    def load_get_html(self,tr):
        if tr == None:
            return
        try:
            selector_tr = etree.HTML(str(tr))
            url = self.source +  selector_tr.xpath('//tr/td[4]/a/@href')[0]
            # print(url)
            response = requests.get(url=url, headers=self.headers).text
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector_tr.xpath('//tr/td[4]/a/text()')
            if title != []:
                title = title[0]
                # try:
                #     status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                # except:
                #     status = '公告'
            else:
                title = None
                # status = '公告'
            status = selector_tr.xpath('//tr/td[2]/text()')
            if status != []:
                status = status[0]
            else:
                status =None
            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            publish_date = selector_tr.xpath('//tr/td[5]/text()')
            if publish_date != []:
                publish_date = publish_date[0]
                # publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            aaa = selector_tr.xpath('//tr/td[1]/text()')
            if aaa != []:
                aaa = aaa[0]
            else:
                aaa = '福建'
            area_name = self.get_area('福建',aaa )
            print(area_name)

            source = self.source

            table = selector.xpath('//*[@id="print-content"]')[0]
            content_html = etree.tostring(table, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['area_name'] = area_name
            retult_dict['source'] = 'http://117.27.88.250:9306/'

            retult_dict['publish_date'] = publish_date

            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '福建省政府采购网'
            retult_dict['en_name'] = 'Fujian Province Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            params = {
                'page':str(page),
            }
            url = self.base_url + 'noticelist/d03180adb4de41acbb063875889f9af1/'
            print(url)

            response = requests.get(url=url, headers=self.headers,params=params).text
            selector = etree.HTML(response)
        except:
            print('load_post error')
            # self.load_get(page)
        else:
            print('第{}页'.format(page))
            tr_ele_li = selector.xpath('//div[@class="wrapTable"]/table/tbody/tr')

            for tr_ele in tr_ele_li:
                tr = etree.tostring(tr_ele, pretty_print=True,encoding='utf-8',method='html').decode('utf-8')
                self.load_get_html(tr)
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
                # {'all_page': 9111},
                {'all_page': self._all_page},
            ]
        count = 4
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # self.load_get(page)
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    task_url_li = [
        # 福建
        {'source': 'http://cz.fjzfcg.gov.cn/', 'base_url':'http://cz.fjzfcg.gov.cn/3500/','all_page':3},
        # 福州
        {'source': 'http://117.27.88.250:9306/','base_url': 'http://117.27.88.250:9306/350100/', 'all_page':3},
        # 厦门
        {'source': 'http://202.109.244.105:8090/','base_url': 'http://202.109.244.105:8090/350200/', 'all_page':3},
        # 莆田
        {'source': 'http://27.155.99.14:9090/', 'base_url': 'http://27.155.99.14:9090/350300/', 'all_page': 3},
        # 三明市
        {'source': 'http://test.smzfcg.gov.cn:8090/', 'base_url': 'http://test.smzfcg.gov.cn:8090/350400/', 'all_page': 3},
        # 泉州
        {'source': 'http://61.131.58.48/', 'base_url': 'http://61.131.58.48/350500/', 'all_page': 3},
        # 漳州
        {'source': 'http://zz.fjzfcg.gov.cn/', 'base_url': 'http://zz.fjzfcg.gov.cn/350600/', 'all_page': 3},
        # 南平市
        {'source': 'http://np.fjzfcg.gov.cn:8090/', 'base_url': 'http://np.fjzfcg.gov.cn:8090/350700/', 'all_page': 3},
        # 龙岩市
        {'source': 'http://222.78.94.11/', 'base_url': 'http://222.78.94.11/350800/', 'all_page': 3},
        # 宁德
        {'source': 'http://218.5.222.40:8090/', 'base_url': 'http://218.5.222.40:8090/350900/', 'all_page': 3},


        ]
    for task_city in task_url_li:

        gb = GovBuy(task_city['source'], task_city['base_url'], task_city['all_page'])
        gb.main()
