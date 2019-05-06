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
    '''宁波政府采购网'''
    def __init__(self):
        name = 'ningbo_nbzfcg_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.nbzfcg.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.nbzfcg.cn/project/NoticeSearch.aspx?Type=3^&Region=^&TenderId=^&NoticeTitle=',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.session = requests.session()

        self.rq = Rdis_Queue(host='localhost', dblist='ningbo_list1', dbset='ningbo_set1')

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
            url = 'http://www.nbzfcg.cn/project/'+selector_tr.xpath('//td[5]/a/@href')[0]
            # print(url)
            response = requests.get(url=url, headers=self.headers).text
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            return
        else:
            title = selector_tr.xpath('//td[5]/a/text()')
            if title != []:
                title = title[0]
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
            a = re.sub(r'<.*?>|\r|\n|\t|\s','',response)
            publish_date = re.findall(r'发布[时间, 日期]{2}：{0,1}(.{10})', a)
            if any(publish_date):
                publish_date = re.sub(r'年|月','-',publish_date[0])
                publish_date = re.sub(r'日','',publish_date)
            else:
                publish_date = None
            area_name = '宁波'

            source = 'http://www.nbzfcg.cn/'

            table = selector.xpath('//*[@id="aspnetForm"]/div[4]/table[1]/tr/td[2]/table[2]')[0]
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
            retult_dict['zh_name'] = '宁波市政府采购网'
            retult_dict['en_name'] = 'Ningbo C Government Procurement'

            # print('列表长度为={}'.format(self.rq.r_len()))
            self.save_to_mongo(retult_dict)

    def load_get(self, params,data):
        try:
            url = 'http://www.nbzfcg.cn/project/NoticeSearch.aspx'
            response = requests.post(url=url, headers=self.headers, data=data,params=params).text
            selector = etree.HTML(response)
        except:
            print('load_post error')
            self.load_get(params, data)
        else:
            tr_ele_li = selector.xpath ('//*[@id="ctl00_ContentPlaceHolder3_gdvNotice3"]/tr')
            for tr_ele in tr_ele_li:
                tr = etree.tostring (tr_ele, pretty_print=True, encoding='utf-8', method='html').decode ('utf-8')
                self.load_get_html (tr)

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
                # {'type': 1,'all_page': 65},
                # {'type': 2,'all_page': 2954},
                # {'type': 3,'all_page': 2227},

                {'type': 1,'all_page': 2},
                {'type': 2,'all_page': 3},
                {'type': 3,'all_page': 3},
            ]
        count = 1
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                params = (
                    ('Type', task['type']),
                    ('Region', ''),
                    ('TenderId', ''),
                    ('NoticeTitle', ''),
                )
                data = {
                    '__VIEWSTATE': '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',
                    '__EVENTTARGET': 'ctl00$ContentPlaceHolder3$gdvNotice3$ctl18$AspNetPager1',
                    '__EVENTARGUMENT': page,
                    'ctl00$ddlNoticeCategory': 1,
                    'ctl00$TextBox1': '',
                    'ctl00$ContentPlaceHolder3$gdvNotice3$ctl18$AspNetPager1_input': 2
                }
                try:
                    self.load_get(params, data)
                    # spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                    # gevent.joinall(spawns)
                    print('第{}页'.format(page))
                except Exception as e:
                    print(e)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
