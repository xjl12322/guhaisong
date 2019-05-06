import gevent
from gevent import monkey
monkey.patch_all()
from lxml import etree
import datetime
import hashlib
import pymongo

import requests
from utils.redis_tool import Rdis_Queue
import re
import threading
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''黑龙江政府采购网'''
    def __init__(self):
        name = 'heilongjiang_hljcg_gov_cn'
        self.coll = StorageSetting(name)

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.hljcg.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.hljcg.gov.cn/xwzs^!queryXwxxqx.action',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.rq = Rdis_Queue(host='localhost', dblist='heilongjiang_list1', dbset='heilongjiang_set1')

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

    def load_get_html(self, url):
        if url == None:
            return
        try:
            response = requests.get(url=url, headers=self.headers,allow_redirects=False).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            self.load_get_html(url)
        else:
            # print(response)

            title = selector.xpath('//div[@class="mtt"]/p[1]/text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',title[0])
                try:
                    status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//div[@class="mtt"]/p[2]/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
            else:
                publish_date = None
            area_name = self.get_area('黑龙江',title)
            source = 'http://www.hljcg.gov.cn/'
            table_ele  = selector.xpath('//div[@class="xxej"]')
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
            retult_dict['zh_name'] = '黑龙江省政府采购网'
            retult_dict['en_name'] = 'Heilongjiang Government Procurement'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,lbbh, page):
        try:
            data = [
                ('xwzsPage.pageNo', page),
                ('xwzsPage.pageSize', '20'),
                ('xwzsPage.pageCount', '1293'),
                ('lbbh', lbbh),
                ('xwzsPage.LBBH', lbbh),
                ('xwzsPage.zlbh', ''),
                ('xwzsPage.GJZ', ''),
            ]
            url = 'http://www.hljcg.gov.cn/xwzs!queryXwxxqx.action'
            response = requests.post(url=url, headers=self.headers, data=data).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(lbbh, page)
        else:
            print('第{}页'.format(page))
            url_li = selector.xpath('//div[@class="yahoo"]/div/span[1]/a/@onclick')

            for url in url_li:
                urls = re.findall(r"href='(.*?)'", url)[0]
                urls = 'http://www.hljcg.gov.cn' + urls
                self.load_get_html(urls)
                # if not self.rq.in_rset(pid):
                #     self.rq.add_to_rset(pid)
                #     self.rq.pull_to_rlist(pid)

    def init(self):
        count = 6
        while self.is_running():
            if self.rq.r_len() <= count:
                count = 1
            try:
                spawns = [gevent.spawn(self.load_get_html, self.rq.get_to_rlist()) for i in range(count)]
                gevent.joinall(spawns)
            except Exception as e:
                print(e)

    def run(self):
        # print(os.getppid())
        # threading.Thread(target=self.init).start()
        task_li = [
                #{'lbbh':'4','all_page': 1293},
                #{'lbbh':'30','all_page': 26},
                #{'lbbh':'99','all_page': 112},
                #{'lbbh':'98','all_page': 18},
                #{'lbbh':'5','all_page': 668},
                 {'lbbh':'4','all_page': 2},
                 {'lbbh':'30','all_page': 1},
                 {'lbbh':'99','all_page': 1},
                 {'lbbh':'98','all_page': 1},
                 {'lbbh':'5','all_page': 2},
            ]
        count = 3
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    lbbh = task['lbbh']
                    spawns = [gevent.spawn(self.load_get, lbbh, page + i) for i in range(count)]
                    gevent.joinall(spawns)
                    # print('第{}页'.format(page))
                except Exception as e:
                    print(e)

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()


