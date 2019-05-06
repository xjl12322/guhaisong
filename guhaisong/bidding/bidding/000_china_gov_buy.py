from lxml import etree
import time
import datetime
import hashlib
import gevent
from gevent import monkey
monkey.patch_all()
import requests
from utils.redis_tool import Rdis_Queue
import re
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting

class GovBuy(object):
    '''中国政府采购网'''
    def __init__(self):
        name = 'china_ccgp_gov_cn'
        self.coll = StorageSetting(name)

        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://search.ccgp.gov.cn/bxsearch?searchtype=1^&page_index=1^&bidSort=0^&buyerName=^&projectId=^&pinMu=0^&bidType=0^&dbselect=bidx^&kw=^&start_time=2018^%^3A02^%^3A06^&end_time=2018^%^3A08^%^3A07^&timeType=5^&displayZone=^&zoneId=^&pppStatus=0^&agentName=',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

        self.rq = Rdis_Queue(host='localhost', dblist='china_list1', dbset='china_set1')

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
            response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
            self.load_get_html(url)
        else:
            # print(response)

            title = selector.xpath('//h2[@class="tc"]/text()')
            if title != []:
                title = re.sub(r'\r|\n|\s','',title[0])
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

            publish_date = selector.xpath('//p[@class="tc"]//text()')
            if publish_date != []:
                publish_date = re.sub(r'年|月','-',re.search(r'(\d{4}年\d+月\d{1,2})',''.join(publish_date)).group())
            else:
                publish_date = None
            # print(publish_date)
            area_name = self.get_area('中国',title)


            source = 'http://www.ccgp.gov.cn/'

            table_ele  = selector.xpath('//div[@class="vF_detail_main"]')
            if table_ele != []:
                table_ele = table_ele[0]
            else:
                return
            content_html = etree.tostring(table_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')

            table_ele_detail  = selector.xpath('//div[@class="vF_detail_content"]')
            if table_ele_detail != []:
                table_ele_detail = table_ele_detail[0]
            else:
                return
            detail_content_html = etree.tostring(table_ele_detail, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
            detail_content = ''.join(etree.HTML(detail_content_html).xpath('//text()'))

            table_ele  = selector.xpath('//div[@class="table"]')
            if table_ele != []:
                table_ele = table_ele[0]
            else:
                return
            table_html = etree.tostring(table_ele, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
            table = ''.join(etree.HTML(table_html).xpath('//text()'))

            retult_dict = dict()
            retult_dict['_id'] = _id
            retult_dict['title'] = title
            retult_dict['status'] = status
            retult_dict['area_name'] = area_name
            retult_dict['source'] = source
            retult_dict['publish_date'] = publish_date
            retult_dict['detail_url'] = url
            retult_dict['content_html'] = str(content_html)
            retult_dict['detail_content_html'] = str(detail_content_html)
            retult_dict['detail_content'] = detail_content
            retult_dict['table_html'] = str(table_html)
            retult_dict['table'] = table
            retult_dict['create_time'] = self.now_time()
            retult_dict['zh_name'] = '中国政府采购网'
            retult_dict['en_name'] = 'China Government Procurement'


            self.save_to_mongo(retult_dict)

    def load_get(self, page):
        try:
            url = 'http://search.ccgp.gov.cn/bxsearch'

            params = {
                'searchtype': 1,
                'page_index': page,
                'bidSort': 0,
                'buyerName': '',
                'projectId': '',
                'pinMu': 0,
                'bidType': 0,
                'dbselect': 'bidx',
                'kw': '',
                'start_time': '2018:08:07',
                'end_time': '2018:12:31',
                'timeType': 5,
                'displayZone': '',
                'zoneId': '',
                'pppStatus': 0,
                'agentName': '',
            }
            response = requests.get(url=url, headers=self.headers, params=params).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('load_get error:{}'.format(e))
            self.load_get(page)
        else:
            print('第{}页'.format(page))
            url_li = selector.xpath('//ul[@class="vT-srch-result-list-bid"]/li/a/@href')

            for url in url_li:
                self.load_get_html(url)

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
                {'all_page': 20},

            ]
        count = 2
        for task in task_li:
            for page in range(1, task['all_page'] + 1, count):
                try:
                    # lbbh = task['lbbh']

                    # self.load_get(categoryId, page)

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


