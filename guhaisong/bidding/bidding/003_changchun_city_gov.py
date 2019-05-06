
import gevent
from gevent import monkey; monkey.patch_all()
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
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''长春-政府采购网'''
    def __init__(self):
        name = 'changchun_cczfcg_gov_cn'
        self.coll = StorageSetting(name)

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            # 'Referer': 'http://www.cczfcg.gov.cn/article/bid_list.action?__fp=vKUU60vQmvMBON82huO8GA^%^3D^%^3D^&field=2^&title=^&d-16544-p=3^&getList=^&getList=^%^E6^%^90^%^9C^%^E7^%^B4^%^A2^&_sourcePage=QGlMpvcgcewgbrz1QGkYn6WfINWh0k0sL4lzLkek3lM^%^3D^&type=2',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'X-Requested-With': 'ShockwaveFlash/30.0.0.134',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='changchun_list1', dbset='changchun_set1')

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
            response = self.session.get(url=url, headers=self.headers).text
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            # print(response)
            title = selector.xpath('//*[@id="wrap"]/div[1]/div[2]/div/div[2]/center/span/text()')
            if title == []:
                title = selector.xpath('//*[@id="wrap"]/div[1]/div[2]/div/div[2]/table[1]/caption/text()')
                if title != []:
                    title = title[0]
                    try:
                        status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                    except:
                        status = '公告'
                else:
                    title = None
                    status = '公告'
            else:
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
                title = title[0]
            # print(title)
            # print(url)

            _id = self.hash_to_md5(title)

            publish_date = selector.xpath('//*[@id="wrap"]/div[1]/div[2]/div/div[2]/p[2]/text()')

            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='details')

            area_name = self.get_area('长春', title)

            source = 'http://www.cczfcg.gov.cn'

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
            retult_dict['zh_name'] = '长春市政府采购网'
            retult_dict['en_name'] = 'Changchun City Government Procurement'

            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, params):
        try:
            url = 'http://www.cczfcg.gov.cn/article/bid_list.action'
            response = self.session.get(url=url, headers=self.headers, params=params).text
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
        else:
            url_li = selector.xpath('//*[@id="row"]/tbody/tr/td/a/@href')
            for url in url_li:
                urls = 'http://www.cczfcg.gov.cn' + url
                # print(urls)
                # print(urls)
                self.load_get_html(urls)
                # if not self.rq.in_rset(urls):
                #     self.rq.add_to_rset(urls)
                #     self.rq.pull_to_rlist(urls)


    def init(self):
        count = 1
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
                #{'type':1,'field':1,'all_page': 35},
                #{'type':1,'field':2,'all_page': 129},
                #{'type':2,'field':1,'all_page': 32},
                #{'type':2,'field':2,'all_page': 130},
                 {'type':1,'field':1,'all_page': 1},
                 {'type':1,'field':2,'all_page': 1},
                 {'type':2,'field':1,'all_page': 1},
                 {'type':2,'field':2,'all_page': 1},

            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                params = {
                    'field': task['field'],
                    'title':'',
                    'd-16544-p': str(page),
                    'getList': '搜索',
                    'type': task['type'],
                    '__fp': 'V7VgOK3HYWUBON82huO8GA ==',
                    '_sourcePage': '1dxhayx - Cv4gbrz1QGkYn6WfINWh0k0sL4lzLkek3lM =',
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




