# coding:utf-8

from lxml import etree
import time
import datetime
import hashlib
import re, requests
from utils.cpca import *
from new_spider.conf import save_temp_info, proxy_api

class SpiderMeta(object):
    def __init__(self):
        self.config = None
        self.history_count = 0
    
    @property
    def is_running(self):
        if self.history_count <= 30:
            return True
        else:
            return False
    
    @property
    def proxies(self,retrys=0):
        try:
            proxy = requests.get ('http://10.122.44.109:8082/get').text
            if len (proxy) > 30 or len (proxy) < 6:
                raise EOFError ('代理池错误')
        except:
            time.sleep (1)
            return self.proxies (retrys + 1) if retrys <= 10 else None
        else:
            proxiess = {'http': 'http://' + proxy, 'https': 'http://' + proxy}
            # print (proxiess)
            return proxiess
        
    def hash_to_md5(self, sign_str):
        m = hashlib.md5()
        sign_str = sign_str.encode('utf-8')
        m.update(sign_str)
        sign = m.hexdigest()
        return sign

    def now_time(self,last_day=None):
        time_stamp = datetime.datetime.now()
        
        if last_day == None:
            date = time_stamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_time = time_stamp - datetime.timedelta(days=last_day)
            date = last_time.strftime('%Y-%m-%d %H:%M:%S')
        return date
    
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
    
    def parse_info(self,parse_info=None):
        save_temp_info['zh_name'] = self.config['zh_name']
        save_temp_info['en_name'] = self.config['en_name']
        save_temp_info['source'] = self.config['source']
        save_temp_info['create_time'] = self.now_time()
        
        if parse_info != None:
            save_temp_info[parse_info['key']] = re.sub(r'\r|\n|\t|\s','',''.join(etree.HTML(parse_info['res']).xpath(parse_info['rule'])).strip())
        
        
    def _tostrings(self,res,rule):
        res_li = []
        selector = etree.HTML(res)
        tr_ele_li = selector.xpath (rule)
        for tr_ele in tr_ele_li:
            tr = etree.tostring (tr_ele, pretty_print=True, encoding='utf-8', method='html').decode ('utf-8')
            res_li.append(tr)
        return res_li
        




