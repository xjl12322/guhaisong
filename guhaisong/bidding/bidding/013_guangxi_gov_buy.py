import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
from six.moves import queue
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
    '''广西政府采购网'''
    def __init__(self):
        name = 'guangxi_gxzfcg_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.gxzfcg.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://www.gxzfcg.gov.cn/CmsNewsController/search/chnlCodes-/distin-/beginDate-0/endDate-0/p-20/c-3/0-0.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.session = requests.session()


        self.rq = Rdis_Queue(host='localhost', dblist='guangxi_list1', dbset='guangxi_set1')


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

    def load_get(self,url):
        try:
            data = [
                ('searchKey', ''),
                ('title', ''),
                ('str1', 'undefined'),
                ('str2', 'undefined'),
                ('cmsNews.title', ''),
                ('cmsNews.buyerName', ''),
                ('cmsNews.str2', ''),
                ('cmsNews.str3', ''),
                ('cmsNews.str1', ''),
                ('cmsNews.str5', ''),
                ('cmsNews.str6', ''),
                ('cmsNews.str8', ''),
                ('cmsNews.agentName', ''),
                ('cmsNews.startPubdate', ''),
                ('cmsNews.endPubdate', ''),
            ]
            response = self.session.post(url=url, headers=self.headers,data=data).content.decode('utf-8')
            selector = etree.HTML(response)
            url_li = selector.xpath('//*[@id="channelBody"]/div[2]/ul/li/a/@href')
        except:
            print('load_post error')
        else:
            for url in url_li:
                url = 'http://www.gxzfcg.gov.cn'+ url
                if not self.rq.in_rset(url):
                    self.rq.add_to_rset(url)
                    self.rq.pull_to_rlist(url)


    def load_get_html(self,url):
        try:
            response = self.session.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:'.format(e))
        else:
            # try:
            title = selector.xpath('//*[@id="bodyMain"]/div/div/div[2]/div[2]/div[1]/h1/text()')
            # print(title)
            if title != []:
                title = title[0]
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//*[@id="bodyMain"]/div/div/div[2]/div[2]/div[1]/span//text()')
            if publish_date != []:
                publish_date = re.search(r'(\d+\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            # print(publish_date)
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='frameReport')
            if content_html == None:
                raise EOFError

            source = 'http://www.gxzfcg.gov.cn/'
            area_name = self.get_area('广西', title)

            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['publish_date'] = publish_date
            retult_dict['source'] = source
            retult_dict['area_name'] = area_name
            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '广西壮族自治区政府采购网 '
            retult_dict['en_name'] = 'Guangxi Zhuang National Government Procurement'

            # print(retult_dict)
            #
            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)

    def init(self):
        count = 3
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            try:
                # self.load_get_html(self.rq.get_to_rlist())
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        threading.Thread(target=self.init).start()
        task_li = [
                # {'all_page': 49876},
                {'all_page': 5},
            ]
        for task in task_li:
            for page in range(1,task['all_page'] + 1):
                url = 'http://www.gxzfcg.gov.cn/CmsNewsController/search/chnlCodes-/distin-/beginDate-0/endDate-0/p-20/c-'+str(page)+'/0-0.html'
                self.load_get(url)
                print('第{}页'.format(page))

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()


    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
