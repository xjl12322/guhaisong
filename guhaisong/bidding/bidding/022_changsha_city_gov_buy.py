import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
import datetime
import hashlib

from utils.redis_tool import Rdis_Queue
import re
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting


class GovBuy(object):
    '''长沙政府采购网'''
    def __init__(self):
        name = 'changsha_changs_ccgp-hunan_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://changs.ccgp-hunan.gov.cn:8717',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://changs.ccgp-hunan.gov.cn:8717/noticeAction!showSub_gonggaolist.action',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }
        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='changsha_list1', dbset='changsha_set1')

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
        try:
            selector_li = etree.HTML(str(li))
            url_li = selector_li.xpath ('//a[@class="header"]/@href')

            if any(url_li):
                url = 'http://changs.ccgp-hunan.gov.cn' + url_li[0]
            else:
                return
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            title = selector_li.xpath('//a[@class="header"]/@title')
            if title != []:
                title = title[0]
            else:
                title = ''
            status = selector_li.xpath('//div[@class="meta"]/div[1]/text()')
            if status != []:
                status = re.sub(r'\[|\]|\r|\n|\t|\s','',''.join(status))
            else:
                status = ''
            _id = self.hash_to_md5(url)

            publish_date_li = selector_li.xpath('//div/a[2]/span/text()')
            if publish_date_li != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d+)',''.join(publish_date_li)).group()
            else:
                publish_date = ''

            # area_name = self.get_area('武汉', ''.join(publish_date_li))
            area_name = '长沙'
            source = 'http://changs.ccgp-hunan.gov.cn'

            table = selector.xpath('//*[@id="top"]/div[2]/div/div')[0]
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
            retult_dict['zh_name'] = '长沙市政府采购网'
            retult_dict['en_name'] = 'Changsha Government Procurement'

            print(retult_dict)

            self.save_to_mongo(retult_dict)


    def load_get(self, page):
        now = datetime.datetime.now ()
        yesterday_datetime = now - datetime.timedelta(days=7)
        start_date = yesterday_datetime.strftime ("%Y-%m-%d")
        params = {
            'basic_area': 'changsha',
            'basic_datetime__start': start_date,
            'categoryId': '184',
            'from': 'changs',
            'pageNo': page,
        }
        try:
            # url = 'http://changs.ccgp-hunan.gov.cn/noticeAction!showSub_gonggaolist.action'
            url = 'http://changs.ccgp-hunan.gov.cn/gp/cms/11/search.do'
            response = requests.get(url=url, headers=self.headers, params=params).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e: 
            print('load_post error{}'.format(e))
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            # print(response)
            tr_ele_li = selector.xpath('//*[@id="advancedSearchResult"]/div/div/div[1]/div')

            for tr_ele in tr_ele_li:
                tr = etree.tostring(tr_ele, pretty_print=True, encoding='utf-8', method='html').decode('utf-8')
                self.load_get_html(tr)

    def run(self):
        task_li = [
                # {'all_page': 4122},
                {'all_page': 3},
            ]
        count = 2
        for task in task_li:
            print(task)
            for page in range(1, task['all_page'] + 1, count):
                try:
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()



