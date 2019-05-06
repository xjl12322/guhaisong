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
    '''江西政府采购网'''
    def __init__(self):
        name = 'jiangxi_ccgp-jiangxi_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://ccgp-jiangxi.gov.cn/web/jyxx/002006/jyxx.html',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='jiangxi_list1', dbset='jiangxi_set1')

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

    def load_get_html(self,data_dict):
        # {'categorynum': '002006005',
        # 'infoid': '99c03675-a099-412e-b97b-7d45ee9c3872',
        # 'postdate': '2018-06-08',
        # 'title': '[省本级]江西科技师范大学工程造价软件升级更新项目单一来源采购征求意见公示'}
        try:
            publish_date = data_dict['postdate']
            url = 'http://ccgp-jiangxi.gov.cn/web/jyxx/002006/'+ data_dict['categorynum']+'/'+ ''.join(publish_date.split('-'))+'/'+ data_dict['infoid'] + '.html'
            # print(url)
            response = requests.get(url=url, headers=self.headers)
            if response.status_code ==404:
                return
            selector = etree.HTML(response.text)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = data_dict['title']
            try:
                status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
            except:
                status = '公告'

            # print(title)
            # print(status)
            _id = self.hash_to_md5(url)
            # print(publish_date)
            area_name = '江西'

            source = 'http://ccgp-jiangxi.gov.cn/'
            table = selector.xpath('//div[@class="ewb-detail-box"]')[0]
            content_html = etree.tostring(table, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

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
            retult_dict['zh_name'] = '江西省政府采购网'
            retult_dict['en_name'] = 'Jiangxi Province Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        try:
            params = (
                ('response', 'application/json'),
                ('pageIndex', page),
                ('pageSize', '22'),
                ('area', ''),
                ('prepostDate', ''),
                ('nxtpostDate', ''),
                ('xxTitle', ''),
                ('categorynum', '002006'),
            )
            url = 'http://ccgp-jiangxi.gov.cn/jxzfcg/services/JyxxWebservice/getList'
            response = requests.get(url=url, headers=self.headers,params=params).json()
        except:
            print('load_post error')
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            # print(response)
            response_li = eval(response['return'])['Table']

            for data_dict in response_li:
                self.load_get_html(data_dict)
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
                # {'all_page': 3156},
                {'all_page': 3},

            ]
        count = 1
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
    gb = GovBuy()
    gb.main()
