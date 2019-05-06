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
import json

class GovBuy(object):
    '''成都公共资源交易信息网'''
    def __init__(self):
        name = 'chengdu_cdggzy_com'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.headers = {
            'Origin': 'https://www.cdggzy.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'X-MicrosoftAjax': 'Delta=true',
            'Referer': 'https://www.cdggzy.com/site/Notice/ZFCG/NoticeList.aspx',
        }

        # self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='chengdu_list1', dbset='chengdu_set1')

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

    def load_get_html(self, div_str):
        if div_str == None:
            return
        try:
            selector_div = etree.HTML(str(div_str))
            url = 'https://www.cdggzy.com/site/Notice/ZFCG/'+selector_div.xpath('//div/div/a/@href')[0]
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            print(url)
            # self.load_get_html(url)
        else:
            title = selector_div.xpath('//div/div/a/text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',title[0])
                try:
                    status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            # print(title)
            # print(status)

            _id = self.hash_to_md5(url)

            publish_date = selector_div.xpath('//div[@class="publishtime"]/text()')
            if publish_date != []:
                publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
                # publish_date = re.sub(r'\/','-',re.search(r'(\d{8}|\d{4}\/\d+\/\d{1,2})',''.join(publish_date)).group())
                # if '-' not in publish_date:
                #     publish_date = '{}-{}-{}'.format(publish_date[0:4],publish_date[4:6], publish_date[6:8])
            else:
                publish_date = None
            # print(publish_date)
            # area_name = self.get_area('云南',title)
            area_name = '四川-成都'
            # print(area_name)

            source = 'https://www.cdggzy.com/'

            table_ele  = selector.xpath('//div[@class="background-white"]')
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
            retult_dict['zh_name'] = '成都市公共资源交易服务中心'
            retult_dict['en_name'] = 'Chengdu Public resource'
            # print(retult_dict)

            # print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        try:
            url = 'https://www.cdggzy.com/site/Notice/ZFCG/NoticeList.aspx'

            data = {
                'ctl00$ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$Pager',
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$Pager',
                '__EVENTARGUMENT': page,
                '__VIEWSTATE': '/wEPDwULLTE4NjQzNjA3NjYPZBYCZg9kFgICAw9kFgQCAw9kFgICBw8WAh4EVGV4dAXlMTx1bCBjbGFzcz0nbmF2IG5hdi1waWxscyBuYXYtanVzdGlmaWVkJz48bGk+PGEgaHJlZj0nL2luZGV4LmFzcHgnPummlumhtTwvYT48c3Bhbj48L3NwYW4+PC9saT48bGkgIGNsYXNzPSJ1bF9tZW51Ij48YSAgaGVyZj0nIyc+5pS/5Yqh5YWs5byAPC9hPjx0YWJsZT4gPHRyPjx0ZD48ZGl2PuS4reW/g+amguWGtTwvZGl2PjwvdGQ+PHRkICAgY2xhc3M9Im1ldW4taXRlbi1ib2R5Ij48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9HZW5lcmFsL0luZGV4LmFzcHg/Y2lkPTAwMDEwMDAxMDAwMTAwMDQiIHRhcmdldD0iX2JsYW5rIj7kuK3lv4PnroDku4s8L2E+PC9kaXY+PGRpdj48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL3NpdGUvR2VuZXJhbC9JbmRleC5hc3B4P2NpZD0wMDAxMDAwMTAwMDEwMDAyIiB0YXJnZXQ9Il9ibGFuayI+6aKG5a+85YiG5belPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL0dlbmVyYWwvSW5kZXguYXNweD9jaWQ9MDAwMTAwMDEwMDAxMDAwMyIgdGFyZ2V0PSJfYmxhbmsiPuiBlOezu+aWueW8jzwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9HZW5lcmFsL0luZGV4LmFzcHg/Y2lkPTAwMDEwMDAxMDAwMTAwMDEiIHRhcmdldD0iX2JsYW5rIj7pg6jpl6jorr7nva48L2E+PC9kaXY+PC90ZD48L3RyPiA8dHI+PHRkPjxkaXY+5paw6Ze75Yqo5oCBPC9kaXY+PC90ZD48dGQgICBjbGFzcz0ibWV1bi1pdGVuLWJvZHkiPjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL09wZW5Hb3Zlcm5tZW50L0xpc3QuYXNweD9jaWQ9MDAwMTAwMDEwMDAyMDAwMSIgdGFyZ2V0PSJfYmxhbmsiPuW3peS9nOWKqOaAgTwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9PcGVuR292ZXJubWVudC9MaXN0LmFzcHg/Y2lkPTAwMDEwMDAxMDAwMjAwMDMiIHRhcmdldD0iX2JsYW5rIj7kv6HnlKjkv6Hmga88L2E+PC9kaXY+PC90ZD48L3RyPiA8dHI+PHRkPjxkaXY+5pS/5Yqh5YWs5byAPC9kaXY+PC90ZD48dGQgICBjbGFzcz0ibWV1bi1pdGVuLWJvZHkiPjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL09wZW5Hb3Zlcm5tZW50L0xpc3QuYXNweD9jaWQ9MDAwMTAwMDEwMDAzMDAwMSIgdGFyZ2V0PSJfYmxhbmsiPuWFrOW8gOS/nemanDwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9PcGVuR292ZXJubWVudC9MaXN0LmFzcHg/Y2lkPTAwMDEwMDAxMDAwMzAwMDIiIHRhcmdldD0iX2JsYW5rIj7orqHliJLmgLvnu5M8L2E+PC9kaXY+PGRpdj48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL3NpdGUvT3BlbkdvdmVybm1lbnQvTGlzdC5hc3B4P2NpZD0wMDAxMDAwMTAwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+5Lq65LqL5L+h5oGvPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL09wZW5Hb3Zlcm5tZW50L0xpc3QuYXNweD9jaWQ9MDAwMTAwMDEwMDAzMDAwNCIgdGFyZ2V0PSJfYmxhbmsiPui0ouaUv+i1hOmHkTwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHA6Ly9nay5jaGVuZ2R1Lmdvdi5jbi9vcGVuQXBwbHkvaW5kZXguYWN0aW9uP2NpZD0wMDAxMDAwMTAwMDMwMDA1IiB0YXJnZXQ9Il9ibGFuayI+5L6d55Sz6K+35YWs5byAPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cDovL2drLmNoZW5nZHUuZ292LmNuL29wZW5TdWdnZXN0aW9uQm94L2luZGV4LmFjdGlvbj9jaWQ9MDAwMTAwMDEwMDAzMDAwNiIgdGFyZ2V0PSJfYmxhbmsiPuWFrOW8gOaEj+ingeeusTwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHA6Ly9nay5jaGVuZ2R1Lmdvdi5jbi9nb3ZJbmZvUHViL2RlcHQuYWN0aW9uP2NsYXNzSWQ9MDcwMzY2IiB0YXJnZXQ9Il9ibGFuayI+5L+h5oGv5YWs5byA5oyH5Y2XPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cDovLzIwMTUuY2hlbmdkdS5nb3YuY24vcG9ydGFscy9ob3RsaW5lL2luZGV4LmRvP2NpZD0wMDAxMDAwMTAwMDMwMDA4IiB0YXJnZXQ9Il9ibGFuayI+5pS/6aOO6KGM6aOO54Ot57q/PC9hPjwvZGl2PjwvdGQ+PC90cj48L3RhYmxlPjwvbGk+PGxpICBjbGFzcz0idWxfbWVudSI+PGEgIGhlcmY9JyMnPuS4muWKoeWKnueQhjwvYT48dGFibGU+IDx0cj48dGQ+PGRpdj7lj5fnkIbkuJrliqE8L2Rpdj48L3RkPjx0ZCAgIGNsYXNzPSJtZXVuLWl0ZW4tYm9keSI+PGRpdj48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL2NlbnRlci9pbmRleC5hc3B4P2NpZD0wMDAyMDAwMTAwMjAwMDEiIHRhcmdldD0iX2JsYW5rIj7pobnnm67nmbvorrA8L2E+PC9kaXY+PGRpdj48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL3NpdGUvU2l0ZVNlYXJjaC9uZXdpbmRleC5hc3B4P2NpZD0wMDAyMDAwMTAwMjAwMDIiIHRhcmdldD0iX2JsYW5rIj7lnLrlnLDmn6Xor6I8L2E+PC9kaXY+PC90ZD48L3RyPiA8dHI+PHRkPjxkaXY+5Lqk5piT5L+h5oGvPC9kaXY+PC90ZD48dGQgICBjbGFzcz0ibWV1bi1pdGVuLWJvZHkiPjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL0pTR0MvTGlzdC5hc3B4IiB0YXJnZXQ9Il9ibGFuayI+5bel56iL5bu66K6+PC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL05vdGljZS9aRkNHL05vdGljZUxpc3QuYXNweCIgdGFyZ2V0PSJfYmxhbmsiPuaUv+W6nOmHh+i0rTwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9MYW5kVHJhZGUvTGFuZExpc3QuYXNweCIgdGFyZ2V0PSJfYmxhbmsiPuWcn+WcsOefv+adgzwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9Bc3NldFJlc291cmNlL0RlYWxOb3RpY2VMaXN0LmFzcHgiIHRhcmdldD0iX2JsYW5rIj7otYTkuqfotYTmupA8L2E+PC9kaXY+PC90ZD48L3RyPiA8dHI+PHRkPjxkaXY+5pu05aSa5Lia5YqhPC9kaXY+PC90ZD48dGQgICBjbGFzcz0ibWV1bi1pdGVuLWJvZHkiPjxkaXY+PGEgaHJlZj0iaHR0cDovL3d3dy5jZGdnenkuY29tL21hbGwvSW5kZXguYXNweD9jaWQ9MDAwMjAwMDEwMDMwMDAxIiB0YXJnZXQ9Il9ibGFuayI+5pS/5bqc6YeH6LSt55S15a2Q5ZWG5Z+OPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9Mb2dpbi5hc3B4P2NpZD0wMDAyMDAwMTAwMzAwMDIiIHRhcmdldD0iX2JsYW5rIj7otYTkuqfotYTmupDnvZHkuIrnq57ku7c8L2E+PC9kaXY+PGRpdj48YSBocmVmPSJodHRwOi8vZ2NwbS5jZGdnenkuY29tOjgwODIvR29uZ0NoZVBNLz9jaWQ9MDAwMjAwMDEwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+5YWs6L2m572R57uc5ouN5Y2WPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL0JhbmtCb3Jyb3cvSW5kZXguYXNweD9jaWQ9MDAwMjAwMDEwMDMwMDA0IiB0YXJnZXQ9Il9ibGFuayI+5pS/6YeH5L+h55So5ouF5L+d6J6N6LWEPC9hPjwvZGl2PjwvdGQ+PC90cj4gPHRyPjx0ZD48ZGl2PuacjeWKoeaMh+W8lTwvZGl2PjwvdGQ+PHRkICAgY2xhc3M9Im1ldW4taXRlbi1ib2R5Ij48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9QbHVzL05vdGljZUxpc3QuYXNweD9jaWQ9MDAwMjAwMDEwMDQwMDAxIiB0YXJnZXQ9Il9ibGFuayI+6YCa55+l5YWs5ZGKPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL0luc3RydWN0aW9uL0luZGV4LmFzcHg/Y2lkPTAwMDIwMDAxMDA0MDAwMiIgdGFyZ2V0PSJfYmxhbmsiPuWKnuS6i+aMh+WNlzwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9Qb2xpY2llc2FuZHJlZ3VsYXRpb25zL0luZGV4LmFzcHg/Y2lkPTAwMDIwMDAxMDA0MDAwMyIgdGFyZ2V0PSJfYmxhbmsiPuaUv+etluazleinhDwvYT48L2Rpdj48ZGl2PjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9DYW96dW8vaW5kZXguYXNweD9jaWQ9MDAwMjAwMDEwMDQwMDA0IiB0YXJnZXQ9Il9ibGFuayI+5pON5L2c5omL5YaMPC9hPjwvZGl2PjxkaXY+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaXRlL0Rvd25DZW50ZXIuYXNweD9jaWQ9MDAwMjAwMDEwMDQwMDA1IiB0YXJnZXQ9Il9ibGFuayI+5LiL6L295LiT5Yy6PC9hPjwvZGl2PjwvdGQ+PC90cj48L3RhYmxlPjwvbGk+PGxpIGNsYXNzPSJ1bF9tZW51Ij48YSB0YXJnZXQ9Il9ibGFuayI+5LqS5Yqo5Lqk5rWBPC9hPjx1bD4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vc2l0ZS9JbnRlcmFjdGlvbi9JbnRlcmFjdGlvbkxpc3QuYXNweD9wdHlwZT0xIiB0YXJnZXQ9Il9ibGFuayI+5Li75Lu75L+h566xPC9hPjwvbGk+IDxsaT48YSBocmVmPSJodHRwOi8vMjAxMy5jZGdnenkuY29tL2FwcDEvdHdvL3dqZGMuanNwP2NpZD0wMDAxMDAwMjAwMDIiIHRhcmdldD0iX2JsYW5rIj7osIPmn6XlvoHpm4Y8L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHA6Ly93ZWliby5jb20vdS8zOTczMzM4ODM2IyEvdS8zOTczMzM4ODM2P2lzX2hvdD0xP2NpZD0wMDAxMDAwMjAwMDMiIHRhcmdldD0iX2JsYW5rIj7mlrDmtarlvq7ljZo8L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHA6Ly90LnFxLmNvbS9jaGVuZ2RvdWdvbmdnb25nP2NpZD0wMDAxMDAwMjAwMDUiIHRhcmdldD0iX2JsYW5rIj7ohb7orq/lvq7ljZo8L2E+PC9saT48L3VsPjwvbGk+PGxpIGNsYXNzPSJ1bF9tZW51Ij48YSB0YXJnZXQ9Il9ibGFuayI+5YiG5Lit5b+DPC9hPjx1bD4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vbG9uZ3F1YW55aT9jaWQ9MDAwMTAwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+6b6Z5rOJ6am/5Yy6PC9hPjwvbGk+IDxsaT48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL3FpbmdiYWlqaWFuZz9jaWQ9MDAwMTAwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+6Z2S55m95rGf5Yy6PC9hPjwvbGk+IDxsaT48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL3hpbmR1P2NpZD0wMDAxMDAwMzAwMDMiIHRhcmdldD0iX2JsYW5rIj7mlrDpg73ljLo8L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vd2Vuamlhbmc/Y2lkPTAwMDEwMDAzMDAwMyIgdGFyZ2V0PSJfYmxhbmsiPua4qeaxn+WMujwvYT48L2xpPiA8bGk+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9zaHVhbmdsaXU/Y2lkPTAwMDEwMDAzMDAwMyIgdGFyZ2V0PSJfYmxhbmsiPuWPjOa1geWMujwvYT48L2xpPiA8bGk+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9waWR1P2NpZD0wMDAxMDAwMzAwMDMiIHRhcmdldD0iX2JsYW5rIj7pg6vpg73ljLo8L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vamlhbnlhbmc/Y2lkPTAwMDEwMDAzMDAwMyIgdGFyZ2V0PSJfYmxhbmsiPueugOmYs+W4gjwvYT48L2xpPiA8bGk+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9kdWppYW5neWFuP2NpZD0wMDAxMDAwMzAwMDMiIHRhcmdldD0iX2JsYW5rIj7pg73msZ/loLDluII8L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vcGVuZ3pob3U/Y2lkPTAwMDEwMDAzMDAwMyIgdGFyZ2V0PSJfYmxhbmsiPuW9reW3nuW4gjwvYT48L2xpPiA8bGk+PGEgaHJlZj0iaHR0cHM6Ly93d3cuY2RnZ3p5LmNvbS9xaW9uZ2xhaT9jaWQ9MDAwMTAwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+6YKb5bSD5biCPC9hPjwvbGk+IDxsaT48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL2Nob25nemhvdT9jaWQ9MDAwMTAwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+5bSH5bee5biCPC9hPjwvbGk+IDxsaT48YSBocmVmPSJodHRwczovL3d3dy5jZGdnenkuY29tL2ppbmd0YW5nP2NpZD0wMDAxMDAwMzAwMDMiIHRhcmdldD0iX2JsYW5rIj7ph5HloILljr88L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20veGluamluP2NpZD0wMDAxMDAwMzAwMDMiIHRhcmdldD0iX2JsYW5rIj7mlrDmtKXljr88L2E+PC9saT4gPGxpPjxhIGhyZWY9Imh0dHBzOi8vd3d3LmNkZ2d6eS5jb20vZGF5aT9jaWQ9MDAwMTAwMDMwMDAzIiB0YXJnZXQ9Il9ibGFuayI+5aSn6YKR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',
                '__VIEWSTATEGENERATOR': 'F5166C9B',
                '__EVENTVALIDATION': '/wEdAAjEa6zHS0OKvqLluSl519eiZi7H72kkAvPqROrOG28FXID8g/xeCzDZJOPgpGV4zViznYSIw3B963y/xzaOhgoHdty0mXvz7f+9YtBAL8kV3WV246YQ+CegotD9lFFwpmUKfH5ngHtxPmfpcq0XKJP7jDu35o5CUn6umW4JNpE1pxCbKKCQb9hM6qbuC0IpGNA+5My+',
                'ctl00$ContentPlaceHolder1$displaytypeval': '0',
                'ctl00$ContentPlaceHolder1$displaystateval': '0',
                'ctl00$ContentPlaceHolder1$dealaddressval': '0',
                'ctl00$ContentPlaceHolder1$keyword':'',
                '__ASYNCPOST': 'true',
            }

            response = requests.post(url=url, headers=self.headers, data=data).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(categoryId, types, page)
        else:
            print('第{}页'.format(page))
            div_li = selector.xpath('//div[@class="row contentitem"]')
            for div in div_li:
                div_str = etree.tostring(div, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
                self.load_get_html(div_str)

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
                # {'categoryId':'', 'types':'','all_page': 801},
                {'categoryId':'', 'types':'','all_page': 2},
            ]
        count = 2
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
