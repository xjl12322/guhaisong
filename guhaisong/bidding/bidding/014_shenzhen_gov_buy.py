import gevent
from gevent import monkey; monkey.patch_all()
from lxml import etree
from six.moves import queue
import threading
import datetime
import hashlib
import pymongo
import requests
from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''深圳政府采购网'''
    def __init__(self):
        name = 'shenzhen_zfcg_sz_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'http://61.144.227.212/was5/web/search?page=4096^&channelid=261279^&orderby=-DOCRELTIME^&perpage=10^&outlinepage=5^&searchscope=^&timescope=^&timescopecolumn=^&orderby=-DOCRELTIME^&chnlid=^&andsen=^&total=^&orsen=^&exclude=',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'Origin': 'http://61.144.227.212',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.session = requests.session()


        self.rq = Rdis_Queue(host='localhost', dblist='shenzhen_list1', dbset='shenzhen_set1')


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

    def load_get_html(self,url):
        try:
            # print(url)
            response = requests.get(url=url, headers=self.headers).content.decode('gb2312')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:'.format(e))
        else:
            title = selector.xpath('//*[@id="content"]/div/div[2]/div/h4/text()')
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

            publish_date = selector.xpath('//*[@id="content"]/div/div[2]/div/h6/label//text()')
            if publish_date != []:
                publish_date = re.search(r'(\d+\-\d+\-\d+)',''.join(publish_date)).group()
            else:
                publish_date = None
            soup = BeautifulSoup(response)
            content_html = soup.find(class_='main')

            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['publish_date'] = publish_date
            retult_dict['source'] = 'http://www.zfcg.sz.gov.cn/'
            retult_dict['area_name'] = '深圳'

            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '深圳市政府采购监管网 '
            retult_dict['en_name'] = 'Shenzhen Government Procurement'

            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)


    def load_get(self,page):
        try:
            params = (
                ('page', str(page)),
                ('channelid', '261279'),
                ('orderby', ['-DOCRELTIME', '-DOCRELTIME']),
                ('perpage', '10'),
                ('outlinepage', '5'),
                ('searchscope', ''),
                ('timescope', ''),
                ('timescopecolumn', ''),
                ('chnlid', ''),
                ('andsen', ''),
                ('total', ''),
                ('orsen', ''),
                ('exclude', ''),
            )
            data = [
                ('showother', 'false'),
                ('showtype', 'txt'),
                ('classnum', '20'),
                ('classcol', 'CTYPE'),
                ('channelid', '261279'),
                ('orderby', '-DOCRELTIME'),
            ]
            url = 'http://61.144.227.212/was5/web/search'
            response = self.session.post(url=url, headers=self.headers,params=params,data=data).content.decode('utf-8')
            selector = etree.HTML(response)
            url_li = selector.xpath('//div[@class="r_list"]/dl/dd/a/@href')
            print('第{}页'.format(page))
        except:
            print('load_post error')
        else:

            for url in url_li:
                # print(url)
                if not self.rq.in_rset(url):
                    self.rq.add_to_rset(url)
                    self.rq.pull_to_rlist(url)

    def init(self):
        count = 2
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
                # {'all_page': 43879},
                {'all_page': 5},
            ]
        count = 3
        for task in task_li:
            for page in range(1,task['all_page'] + 1, count):
                try:
                    spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                except:
                    pass

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()



    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
