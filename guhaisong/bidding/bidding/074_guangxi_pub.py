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
    '''广西公共资源交易信息网'''
    def __init__(self):
        name = 'guangxi_gxzbtb_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection

        self.cookies = {
            'ASP.NET_SessionId': 'trbofu0uet0aywbdhr35s0x4',
            '__CSRFCOOKIE': '6f7e275f-5762-4569-8ea2-ae98d3b0379d',
        }

        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.gxzbtb.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.gxzbtb.cn/gxzbw/jyxx/001010/001010001/MoreInfo.aspx?CategoryNum=001010001',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        # self.session = requests.session()
        # pq = ProxyQueue()
        # self.pq_run = pq.run()
        # self.proxy_queue = pq.proxy_queue

        self.rq = Rdis_Queue(host='localhost', dblist='guangxi_gxzbtb_cn_list1', dbset='guangxi_gxzbtb_cn_set1')

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
            # selector_div = etree.HTML(str(div))

            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            # print(url)
            # self.load_get_html(url)
        else:
            # print(url)
            title = selector.xpath('//td[@id="tdTitle"]/font//text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',''.join(title))
                try:
                    status = re.search(r'["招标","中标","预","采购","更正","结果","补充","询价"]{1,2}公告$', title).group()
                except:
                    status = '公告'
            else:
                title = None
                status = '公告'

            _id = self.hash_to_md5(url)

            publish_date = selector.xpath('//td[@id="tdTitle"]/font[2]//text()')
            if publish_date != []:
                # publish_date = re.search(r'(\d{4}\-\d+\-\d{1,2})',''.join(publish_date)).group()
                publish_date = re.sub(r'\/','-',re.search(r'(\d{8}|\d{4}\/\d+\/\d{1,2})',''.join(publish_date)).group())
                # if '-' not in publish_date:
                #     publish_date = '{}-{}-{}'.format(publish_date[0:4],publish_date[4:6], publish_date[6:8])
            else:
                publish_date = None
            # print(publish_date, title)
            # area_name = self.get_area('', title)
            area_name = '广西'

            # print(area_name)

            source = 'http://www.gxzbtb.cn/'

            table_ele  = selector.xpath('//table[@id="tblInfo"]')
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
            retult_dict['zh_name'] = '广西壮族自治区公共资源交易中心'
            retult_dict['en_name'] = 'Guangxi Zhuang National Public Resources'
            # print(retult_dict)

            print('列表长度为={}'.format(self.rq.r_len()))

            self.save_to_mongo(retult_dict)

    def load_get(self,categoryId, types, page):
        try:

            params = (
                ('CategoryNum', types),
            )

            data = {
                '__CSRFTOKEN': '/ wEFJDZmN2UyNzVmLTU3NjItNDU2OS04ZWEyLWFlOThkM2IwMzc5ZA ==',
                '__VIEWSTATE': 'z6UhCTu3jqnsz47aHWA7gSWW/wG9YleyN9akSy8SDfrTIhkXv/8D27JYdKJG/ZWKPqb0smc7bS8/xKHcu0vIwbRrxU6DQIlkQJ3m97wtYMFtK8KpjZwIdMqSgnw1q3DjBu9vEraO4xfqzJacAXSCukutXa8BPCyLevI3U1naYHFUSSNqQhNo9cICs8Kqr8n8HNpvSRjqJB8CTAWoGlc8x6IeC/j50VdUETRudT9/w6Xc0To0rsY/yH+VbMRbAzIFlzNvQP/dmUPEdjMSRkvyULU6ZIgal19QWLJXJSGioQKJ3StzC9BqsgyaCobteQoKLs8/h20aMOCs2YO/oSpUVr0AaapTqrGIMhrM/IaPn8N00monNce5uU1fWffkBK6zL4mJijgPTmuyCrA3/AUY5La8VvP1v2NUScoKAdjRaPypTDlh1+ZUt3x7ZdwcmWd7bwgAK42uneSLZWSC7Er0k9VcuPZTR4E/I8fbEzJWf4Bf9pI2hs5actOcnD4ETfu5m/dgfq1mgz4uTrYIRcqE1xOmE3WDJNircnYO4xVTI49MDYfgDcGtjWRiBZHd788/5abVt7h9sXkzXPHboi7zVv4haS8yZsIEeQG3F8MFVtM7H9+/Kbss3uPC5I5V/dDw54S2zejVmbAx9dU68wJfL1+c28EbvOUOWgOE6dCuFmTS3nSiBLMjwUeRtKwhvP1RA5MsKD4WI8JtqR545DULfQz0XJCh1PlO+Nd5L661UuspC/PvgWRoNQEoaVpLJK1S9UuPAdNnAqXdMuJdZZPu60+Jdig7zOBSEGbmwNvmXB0vphagqkqxf1nruFS0OGP/D7OJcbcObzotOwp1GpMmBdqg6hiDh2nccyFZ+E4DUv5NssGK4Zj7dY2jhMBv8bvkIwaY+uLYMLJwJ0DqhNyP2JTKv/FmENt0pjfytL0EU2HRmLTcPgJWgdQ2IZ7GZCYhkSzBfkkJOmVx7t+UZervSy+hZBsVsaz0DpKZ9JMVXfOYVzQNZt+VmcmIn9feEEJH6F8t4gYlC1pvrfcFcBVI8ndumFTtsYjnHhD7gMG8q64rCOoD0DAB0si2OdOndIUczT0RlhLkpqa9RA1nQ9kj75RJGe/dm4NGfCqqUHcRJTNbixZUPdA2pJNzYhRAMLQBqGmFANV+tvqB2yDiJg86H6ouBO7v2+SXxkp70ZBxv8CiAHw2kKEWoxfqmnMi552GiJRSrpOhcw3ylrYA3dINyJjtDJ9ZNYxLGWD5Vzu170wePz/foMZ6o2+8zWgEBc3PDx2l3UTG1TUwt8dbQbokscyKFWtCoo/qs9kkZS1KYBZ2NKe8K3EswLU3d5pHJsUtFhe2QtHhMolkwM3LTzBIIBl1QyPS6HDnCasCFHNbGX2/k/TMPLEBrOpdsRo1YhhhNMYz8pwQbwTxo4WRsmmQBvPUkTSlk04Iasp9Tm8/2WO/NIFs0Y/h0BvdanXJHwP8blNEMZCd5qmP02LdYGygy6hs2uU79m+VM6wtHIbYxkC2AKuDkErEqaOuQCNNiQfyP6e0oaZwNcWQOOaQDWsz9/F12QCDwx3X2ihIaG2v1YCQHKC/lfnBQ8o9Q9LvrLuZ4yjVbaO3B1eM0Q46zuTbT9KbhLwkFm8LH/2JM/OOvvUDNN7A4z42REh3kZWC0eXOyCDD1HvNdOFxluC6GRtEdv6/31i/PKLPr7te5VCIGCFjF9oCxquF9+2ecYtlmqcvbEvCKnPx1JDO1BloI0i8TqwjDmqyaORTTYzrtJwnXjKiX+8TKDC9yyOMXA1qbTt/KZPTpHI1R0P9qQ7Pk8AwKeL1y5g68OMHUqOsSyJuo6SNety/xymBke5m1FG2zE9M7OOqSGtV6NCKXNoSgi3laUmbAMZ8x+GOQnXrfpMGvtPUPIUY9zEvUiEDeKKQSnqlxf5LwEWyWlEuzSjO4+8nIGVC9nUb/YEIM5o2wiC1lMXl2d2tDQ/Mau5M3B6qmSLx5QP3nfjDKsoFqN0tQxlo/TBCKLXAUOHM8zTrEBY/xkb6tvnijW+leCYPSKURnheByCjFWSPnlz6C8tiktma/JzVph5blcc3thpmHiGp87enSqKQkjIf8RJkVeM+ENhg0gAndrokhhPBiS+MTNCuX2zXimlH2dpTY7JKu4uSyltVswpG2mLWFGegTeKLsBjVks8je/eeJvAaevVRh9mNOD4Cj8jh6/6taR2ee0/EjYlDIkrCNstLNBcQ35u7NQOesHpN9j7Zxf1iSsz1ChY/fS3w+3AVg7hnZA6yr1pUa54NWQEakrAgjpNUTzdTkSfyLkGmdqSXZEady89XXYBKDfF6rkDa8hb19ujrWQZn9m9K22OeAw1k3w8wl29I2LMno86bezhCDhZRVa2RrsbsYAtJ+TMnEdWUuINhSrEbe9zRRga2N4BJv+eopnSClJYNNgkMiNVEOdWnfDVa9Wb9iqVRYfjBKfZRv8g4/tlMr6ygKYPBRprLiv1VQT9M+5hkhLWgtGeyOzTGxfiZG6QHnqSL2g/A+nu5Ij3fGoVDEPPj3Adcqk6AUrcY+XaJxR9wVVz927mFfFq5kxjo12Sw2ak1pS7faIy7o9Fk7Y9XKh1qu35ltABHEqiVIeb/dymZ7oLV+AClQeLbbmciJ7NKrdzTwRxanqOirpiPl5MnJtQxROEbt6lYeRG1RzEUsKMlp/L5v2aBRnkVWC4odd6FafVJw1NFDAhtVrI3uGta566tdsuT+FYaXOtELa/hUjBES+jWAJ0+qrDVff6ilka90N5wpQ55cjCwAs1VtaLa6b/zuin4h6+wfwtJnEGBfXND+1AQSbrveJHojhedFjPAYsSG988yhO0A1+TdQWGoJQmlEINiELipfNz/CUCbHENz431cxEjZV6No6qEXLUVXcbXp0BRB8sOZWtmbJ5LaLzS+unRSRN9RMk/80ct6AuINtSE2MCwrBpkrB3DhkebVRwWxxODsfGOj20j5pVpeI8jF75k/9igiTP/+3+N20FTsoJ/fVXevJ2YTUHIrJZc2j3bNDZ6LuHcJbEjS5DQat9WGeZa2FzDRba3ikBTxMevju8T9I2s19yFeztg72WQTcyDhN0I/TryQNcqZq67e8ScokSwQ1pE95EkIBdxk+7J9IIm1KHGp7P1T6PmxBqSyCyJT53AJgQxbhG2N+2NCpIk0ZfKA9Apvg/UfBFli/pa42N1XCdVnLwWW9wOY+vSbuo9Fnf91wTW1SrH1cZCrcWDFzJTlB703WUdA97ZyWuRMwypjXj5RGpTRi1R/maM3DwIcC6ktl+aczr8jK94UVPZ2iNVmgk/Ml92vly8vycYSTkHvFCHmw0gzSyhBjaCDSEL80nw4T4XjrrNfohWQRYDnk+isTfbfmpt6KRz8yIczndwTZdSN5rYigqeAJMd9DAxm28DcGCUk1nOyeASMtByfmPDd/jp6ihDR8Uj10eaty7X0LyjvB3Ol4kjvNucSPwJhwe6PCULDCMKKM9EQFTs0UiiyAhA/1N52njX2EpWDLOnT8yfMMDfDOwdwex/3DVo22nYjzTArBjbjJ4N6RtPW0rrWXJNJFHpm6ZSUTFZXgtZw+wAvBxRWiuXsvQqUYS4a25rN1/8aIaKxV9rxhSTZzF7l9K5S0wvjF1+kwarDs/M5SQT8pZtdEnySC5tgn057VgiCpEHbCWYm16zWPv7ARLsRV8D21nmMoYAJqJ5jZZMcrVTMuutYG7zc7W2rmjt2Nto/enbDGWgBeyMCsCPPA6+VYvOXWV6JTCwwCUQ//+LH4z1Kokk02ObYuNfwh0x4ilnU6JYM9t65ExOl7shHpKQUHrXwtwDi49hZNTD78s3yPOJYa5E9delhUSFFCAqH5/AxgSFKMOJXyBgsQlntLLWlYGCUabX61ClQuf3flIQ80RBZKlwA6qTpW3dS4EcgCP4beaujMVq/ifreAkY3hGwZwbdXViux7rLJTdj188Bim8KVbCYfIwWWoin8Nsi/rZiPorqikSMdyEw9VoWtIMz6/PNeJY5mh68hzeCGFKEIRNDPy+wMlMbh1Q1vzj1RTQa7sMAaDrq99gx3oc+CXHZKpbVwPOk/HwjJ6JM90TNrZdBIL0+PW98LgriR5FuqoUFp4DUHMSW0YjZDqj+MUq9OMFhOCFUTzg53NkBlgvKdzzr8Afve7xL9pXCcvXdRPxCHW78Hj1cJn/zmOe19RissiNTqUS5ArxaCeiD3IEmVKJboz2B2E7kp+mwpjCvx0IJ9HUUGJiBeP2ayo9SGOxZPfKVZ3hLV5Yrk2kyOagPI9ZA7kNzCRQO0+cgObPKve9kqANbcB7CxIWP7yVTTMGN2hHwzK731hA4nU7VXT2af6fO1/A42/DHaqmLqgBNBij6ihMW+xtOUmfJ9Fft/+9fTMps9rvznPluGxp4LwmLiugk9OEg+5qzJMzpec/zYFU0L3GWPiMJpcrBgO4uZ9Sl+beLk11GzbrFgcL+3Uhb7dzgxZvAaE4kHPbx2W4VDJGCuXdiTTlPZFwV2KTE2k7U37bP7IvgRDSu18ZjXqS0ckwDqd/jbXwmc84FLEo73rs9D050kmeYREx9c/GJHs6bR5bTIKkrCorEXJ+I1LNItiyYpgQ0fCsutxe91UwVLh4IV1l+jmjQoOeY99vzYmqJ/mv1FbWuqTSFZzHOIJmxpY3hSHGsnjh3fTlCwp2vb7OI2OcS4hdPfm/wUwiMoO4o0+MEEIZq4s2/243WkXxnQv4x8eGJkbBvhlhKgNOoNxwB5wgAAnhXkH3PH08VS1skVudmUwMNChQMwKnQr44CUMhYsmy3PXftAeLMBvTjSAngfdupJU6mV6hQHcioY+uk3cq0AfBtDdRKa/ANMFXNFt45zbANxG2wtfbaGLKmSETIPxshs5KupcFM+E0ikl+/iO8sLV7tbIqPmgzKG4kuovGfVw/Io8Z+ol113M9419oCHr8M9LZcqOw1HbQcCC2hDQCyW9aiCEryPZyUN0c84vCukRQACb0YeTBu8Hl693+QJd0KVAJ8c05wTRa0xBjdsTdZ2jVGdSez42wtoI/ZaMsjcOFKrjaeMuzH5ZWNJROiawSaucbQfRtrfvIXBDaOacqMEIFp3qU9wlzUYAAJhhHp0I2DeM4moOILIdIS0hflR4p2MLF8VR9TO6sy3qaQ+omHxh4mWqVin/PqYKElWtTbxMOCM5U5sxJHVw+MsnD9lcqpWRyunuYDGtMdDLOXHUxRsoqk7O0X3gB2Pta+ffxXL5yNMsQAMBqzvlO/x6N6gWQxkySjqMwrj+oeKs/uVWuSbxvnsGAkR1k4XobilSn8pN4Tws3cnNH848CYCoLrOEIXGQOFfm5IqLBami3ECbfrxZOnlctJ2O2FMMtM4oKK889EbGznvm76A2lOEmgIMhPDFsNwca6AJRIP+AbZVafFTK/pjG/DQR+Onj5x1ArfG7xkX1GcgsKqlPk1XC+SyBa1Q0/BE+lvrYD7/ozLSA9t87Gsm0/+fFpWr7+Dx7dKA1qQfhE5TU+uhAn5iz6m/4mcH1JTKhW2EZVdLI34Fg8MVPBHDoGwcnYGw54D9UT1dHjUdYKXDmkECVg9t/fGLNAryddSE8gwBmGQPQBCg8ACFDG1Vz7pz4DwtIHtc+vs8Q0tjuCRut2S7fexj9jEXaUHUaUiY9yMHL6g/3X9/7WsxsQ9BVauhusCPC4WjsKkFny/W7felQcWbX9OJ/73kRA78BuG1yWPN1xEkZFe9IWQhMCCOKZ+xXJs7IBi4bsctunx/TyWznFXi5mUtVyLgEG1JAG/7MvLXxyJrg2RhViCrMv/zWdjxuaGL1oPA2JINl9QnSsWFMYJwsUFy93HIP2KIILJzam7R0Q23+Xj0ioiO9tFl5PGAlLJEMhRVREnayraf5PKcmAYJsJNguyoTJhfyFCsC0kA74a9S7YwXiBnr7SLHNuVvBACVyvcSqGsVb/hXDDwzdW+UTXiklYnH5U7POZNSkXq539j+FG71Ndxsxz906PmTb/ZU6d3X1Zlm583SRB8VzYf5qCXrHJCK7d98zytr9XKoUH1rIItoqalLp67udBMEOqRrdiG5GYV/P117dunqKt8cVryDjUuiFfkNNRSSBknnFEVuIXdeFOo/tgfX6AqU5sDmjajo88fRSOnnDkAK0YazroIwporIjp8QxTCv+HLLpt1FsQWnxI7gc1hNaUnzCkTuoTTwLzIAKzJ5iWfgJvu2voRLFZ7crFe8gJ5eCZ3x3O6uvxvkhit0XYFsuPL2A7b4agWGb+fXNbdccCoKVo1mZjI5EX6medskd6mcEEKscxBWb8skl4azvlcA8v4l58nkVF3P6puR3nR+nMlT+igLAEttSfIO4aKH2ry5R4D14InwrKbURhOZOiLmilVjqtTZJ1gI/pLg9F7d4FLpG0qINV+srl1aC56zfI4MkXjroArUE85yO/XmgrqWHS+PIFlUZyAEk7tb0HcK5J/vAt0MGEsya6QGk2+6nBi2QDEdcykbe9GKcJSv4JKlzjngqjh5yjz1PY2Ui4QsuAQYfVpLOJXFtsVyXxl9OnWNAkIcyRdjR+UyJUqeMrJmvCGZvyDkr0heFp+W0XN1aW6fOlB4wURO6wvvmT+f2cOR8e8oRW3UdURs+UPBVQSkaU8fHDFecHkfvruVuN0JhKFDGijcGQEicA2sSHfgSrzv38aOwCUmxsPaSIdLqYlz+Q+GzPkMFQpkQt43C1yLaEh8FSOkixOV/P2Y3q5PsII3yfgdHf6aTGAy3OPK7eWc4Yo/avmsj21hPcJDoJk3iMYGQE/kGwueljbGLkESjROGcbJOe7qwavRbM5Ok+TgKmR1kEeKJ7rU3UWh9Ttz+oBd+SZUXzbphYUvPLH1GLR0J8qW41Yv6WmL7Zg5XMYw6OmCWInmkSCQPoTUEhrkagnscZ7OFpdls0QE7tFTHKmzXU66cAD86BZofRkBTdYI0bk61VLr6hXV81YSBQTBVZu8FkAYYfI40l7FHDi/3fNQQ6vGGlSCz5ULlF4QEeBA5rzPBkzpcK22e+bl6YBOnnpx3N7edak3Auc96oGVFabec8QM3CUI4G98rt3A/OGQw9iu6P8WFfbuBQnCtva4pFCrJorA/6QXda247/pRL7ov5lMMc1qqLrYzxLgTUoYs0CCgIosEhucryWseQ9c5KzY+r0pChkUkKhkmXUxMqO6+5pFZ/ef1Oy4KXQYUMR+RU/obNSHyyB+L70Sw/xJCeGy9d9bCjMmkDL0t9elhkn0unvzObirMrHPh4h4FXYx6rxyfqdcz8w7KsElalaFk4PIQKupZTp+UayvTCKNPwLuaEXQr5tXccra5niBnN+TAWRzWKXefACVlF1xiVE3mhbH/M6gdTYp/Pj6fxWoP7pQG5lolcJsn84BG8yt2DYJUknDNBw992dolm7mpFWDbFySsKcyZfXTl9qxNUTG8ge19reYz+pNZANlWEQf2tG+StIiFZVZkj/X9DQECCuvK1aCPfb7jop14pPtOC9iNIjBG2/MvwoiqsDLz0IZMMA+Yz//STFJBO/mDzll0Js+znxQTl2VOuTxOpZ4SQvPnp2jPxVW/+EaA1PCQhOvy0x2kkH1K+KPsIJkQvLG7XbS0C+qOqvmccjBRN0iwf0DD+tqjYVUZ/EkLd7vtQEKL00HMKkdErClQxRPD/1bTe1aw3OUfegjlohma7sjZCQPrD/7Z81oVOZfLBxTM9kYwx5DdvZP8K2g/v3qjtEac4oT71W/a3yLRGllWEuKf6d08Yq2LrR5jcNy22U0B9R0exyFKegatzOOCoyxzQ4/GRGNuRXdvdnzwZqUCxY4war/yVplduX9R8pq+wZZLvFF9T1AN13JSKbB82LG/D7dMgZpw+Av8ur98jpUn8RoTPWaLAyEVFaYPSy5QT6vDHtXFXD8PVi2ET3uWpKCrVPRiy6sYGHB75XzN2MvXsqvRr7voBo4Rl4TXbZaznSxwxYLzHmIM8XzLekBxOGg+p6ROERQ0Bw0MYscv5TDPunfts+tIU2ykVfyfkt+4wyzX32uOseAi7rn40pXw2fixSAc8lBe3h7myKkGvkn2EkxmKsvs+6ML3TeoTherBgPi+8V3cCgIakdNXCyq7Dm9HeZ4yJEmgWaAHkLZq6C4ZmrJ2ZVXVFc8zxGao/IHFQCrsNMXa4WcnDdLKl/88v9A+W4nLQmDIcvU+rfQKGhBp2XbnEWrzewVw9d8ysuyeqiJyjvjjBIbLK+AZapva7xG74cN9FNuGWOdt7+pxiZes94+9ERUbT/Sxhdca+sGV1E9ueSv8Bw4FZ0l7qFOs2AyO65DUTekPwM3H84MMyRDXrVi733KMjduEnhjQtfoEYidQBuvpOUm5opb7xiVGgtDqtYU/P2D4Ztf1x+n/r7aZqytfI+8CJwKh9qhhgT5NKH4Bp/AuJVJqHsZIdUUNxrUhCprv8RU74Q1y3DimHkHr+yqr3LU7flZ1MnZQF+VZ51PgQTfhrGgsLCs73jPMgv9jLsRpNxs5K7EIThZUiiDMgdP4jicfrsI7e0XT9D9Nmpvwj2flU2pBkGNO9v+1YYpK2hb71KAxj9kE8KrKshiJHv9WU1RqRmWmIfvIvi+BjfaIMeywTCFcMKWFPret7zY8ZhJqvaowFoCyhNiLYWFjvKqeTZbeJti/O7AKjavWn8fa5LoHqGiIQeGjp5izIEbD79R7CaNNmE0suHKFFSjOqU1yrQQ8saoMkT3wHspM4A42gOD/HGFu0fNm/RGNZpBAqHmwOJ/6AhkKU2scSX0QXZrRXhLjABqvBo0z/OcCJSgTx3aUECmBfggWoSJcFUnfREqLlaecxEfme1ZKGkpNvJBwnNCscy9FQfQsgw0ryS1AzcUyX/VNgW/3ny4edpDK8dcVVmXJhft4c1yH+QLA1be0clmpLf64M8t4pkD0LGSXSNL7UqVHfkSiyaSWttwjdGmELYSQohx4nWEsPUO+tze1TYeBlsgVdH6UctVzFTuop5jLUVR3oHOBScFashAOHcDalzVcbzpJ0vn2n7YeCN51+5gPhgzWqd4bP1xNo0Gr0VTCVWpAqoTlRj6HekLhriSxZ6peiDarmlLp40AYGgViIf2Zh7uWa71YEDHlx+MT/VIQxPrSnnbCHGT+a2hzy54AoynEdL73gkCj8JgKce73cjtoPaFfRG+FLk/R+07JI+Al8cV07RwQysZSFZS1nkAvntcMgtBJLudhlc3IMP9k3l6EOxZqHJyZGoOwTfCMjLg2P7Z7SScEpykE+lzWFU0W6O+4OGpE8K/zYbErAdtF7JCLJLVA9AvKCyeDmQGdRGbhcPhnskFIGpL9RNHKZHAh8eTKQdE/Dk/K3+0wPGXD45iCk6lbgu9S5x0uE/kcVWDb3TfrvvoqycGwdnxALI7/lFVlb0sxrDrnNOuEG0canG+RKOKIPJZYa5FyVu1tXpr+2kYvvcsIwxVVzTl7/jOo4Fnmb8b/7QxXfZ3UVVLj+8N+P6M0qUCsiaE3pGnGy1HxEwfC7nIJfki3+tBIBa0hDnw1cxfQi32uvdlqyeV0/VX1O2tg1Dj3ihbMrG2KQ+YTKNjinDUA3QmF3K1ipKk2+xoilF8vuCQaEJVJIaDOOIwX4x+/4d0n1Q68MaLgw5mxK3dv1A8hr60kZ8fYPVvNkMCBeLo7cMVs4swMuVSjM6CxrQsBId/+JktBo7RHJakj7aeWdZ+g8ITxx54oNQutt9+h2QTKGpSDyU0j6kF61rn5M+H3MB1ZN8dLE22fcXjzHFGAKvJzJM/7w5LDQ/Oh/Q0Z66oDeacr+NtAjsok7FIn91NLerbGoy4rjKNc83qyoKwdDmhWrokeneCS5kqgTG2b17cGb1ynyBNKBFTqDtbnkFTK68vsJtP0hzN7hXfINKOTGUEPdKTE5WPyt2ZrYOoz0VnA01EewJa7gXUec6x/kBp7X9240r01ywuRGrw5l+JXtiUmYjOteA7iSqWwbwqnFWwAlBgfXIvw9hcrVN3eXxX4K3fIucHS2ibM3KE/e1VviGkCU8/K2OMzQHOuiQiix9UPiwF4oUGRalHxBchirfetT5yIhGsdLah1X3CyDEaxUA6Cos6rV4gB6ouVnVVw8pqJVY5JX+rYc161tRLFVmtrQZhbstM9Gbc5dJpHJl6xql//rGdgAcEnv5jm2xe2BHY4Wn5y4P5PGeuNe1fKBcnLlgpjK4dHMB0NUfLH4o2E767ZXB8rfndv19ZMfhMIU2E2x+A0MZNhKhy2mefFaj+wQ0OVddKhEoXYMETtGaP0pn2jfwd/r8jBwn62zgNRmZFfhJ4OqbYydTuuhuZQyfZpLlF3uWxE8tqNWWzLRRWTZVwBAzKexPEuzsVIiKkrXX94kYze8kt8KcoDkN19jrSVyomHZMBk94OnNouLVONkXWkDxvDIbVMvXSJs+uqk7228DmhZplBwNSpaVg19q9Ny0vCvio98Dh78Pqi12XYaKRohe7RuJbzUrwunTW4hsV5xAreCy9n2DtRKWWI1v7rw4L/750nS1LtOJXUDbG0FLCpRyHmVhckad+YXGK/V6QtTtVDOp+DqH/7mlgeTkOjzuXej5i03PaZhez4eXw6Cozt0BqmbbaOK7aBv1GdZTWWVlQ7A7fnGGCxFoElmuksWIKIzhwqf89a0Lnk0TjF37f55mvnr5F3XVW4TlVUhsKhsHIANNqb/xKBFdxWSjMJg12V/5DeItXrcpr3pI8KJayTCpBOqbzcfhk+fMjMmDY6/+f1E+nMpqRYfzecMDYwHwpPV0F9DT5xzddj/vFPQMWgR46dz/jVaakX804jDbJ3xCVBGa4EpCLR3Br8Tmi7lA8RKoRgxEayH4PYHpI++Zi+VdU9X5R0ANvWmFqtzzv2XuCg4dPwIwFAfmeisnvis81lF4xei5s7bTlubyuMo13VKRbMAYj92exfPxrwl5N+9qbnmIzidl7/mmGq5pNHJ6zUOXizulKFbnpJw2S65Aun2jmaWdQinTF7Nv+Jxcd+4GSkkUPcQNhIwoE7rIF2PaLBSPFwEYkro/FnxsWElzk8z1ReQikPzMGh4+GnW2dzU0qF+G4X0CNiVewq1of+B6jQotyvLXtmsinINsLZ+EtE1J7ld4El1EMvTPD4hyVHmU5TMlKq320KlRFE9h33vszSAjEmhnM695IoF9R8jlHQ7uDJ7n05l1da3nugwlRewsC5sQtuOQ2+DQq2MKwGKDe/FckChLyWE04XHP+pDmSnNzjzjScWJswnucFfv+ThapwkyJHzGIU6kFd1RXXSnusEkker69Er4NvK4MIYUIqUBXBBIKdOCD/90q8FB/22tu7JITuKl6c3vPlcSI5zUNdClEl99ccvLc2nY9ggGVe028=',
                '__VIEWSTATEGENERATOR': '16D6DBB1',
            '__EVENTTARGET': 'MoreInfoList1$Pager',
            '__EVENTARGUMENT': page,
            '__VIEWSTATEENCRYPTED':'',

            }
            url = 'http://www.gxzbtb.cn/gxzbw/jyxx/{}/MoreInfo.aspx'.format(categoryId)
            response = requests.post(url=url, headers=self.headers, params=params, data=data, cookies=self.cookies).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            # time.sleep(3)
            # self.load_get(categoryId, types, page)
        else:
            print('第{}页'.format(page))
            # div_ele_li = selector.xpath('//ul[@class="ewb-right-item"]/li')
            url_li = selector.xpath('//table[@id="MoreInfoList1_DataGrid1"]/tr/td[2]/a/@href')

            # for div_ele in div_ele_li:
            for url in url_li:
                # div = etree.tostring(div_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
                urls = 'http://www.gxzbtb.cn' + url

                # self.load_get_html(urls)

                if not self.rq.in_rset(urls):
                    self.rq.add_to_rset(urls)
                    self.rq.pull_to_rlist(urls)

    def init(self):
        count = 2
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
        threading.Thread(target=self.init).start()
        flag = 1
        task_li = [
                {'categoryId':'001010/001010001', 'types':'001010001','all_page': flag},
                {'categoryId':'001010/001010002', 'types':'001010002','all_page': flag},
                {'categoryId':'001010/001010004', 'types':'001010004','all_page': flag},
                {'categoryId':'001001/001001001', 'types':'001001001','all_page': flag},
                {'categoryId':'001001/001001002', 'types':'001001002','all_page': flag},
                {'categoryId':'001001/001001004', 'types':'001001004','all_page': flag},
                {'categoryId':'001001/001001005', 'types':'001001005','all_page': flag},
                {'categoryId':'001004/001004001', 'types':'001004001','all_page': flag},
                {'categoryId':'001004/001004002', 'types':'001004002','all_page': flag},
                {'categoryId':'001004/001004004', 'types':'001004004','all_page': flag},
                {'categoryId':'001004/001004005', 'types':'001004005','all_page': flag},
                {'categoryId':'001007/001007001', 'types':'001007001','all_page': flag},
                {'categoryId':'001011/001011001', 'types':'001011001','all_page': flag},
                {'categoryId':'001011/001011002', 'types':'001011002','all_page': flag},
                {'categoryId':'001012/001012001', 'types':'001012001','all_page': flag},

            ]
        count = 1
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

        if self.rq.r_len() > 0:
            threading.Thread(target=self.init).start()

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
