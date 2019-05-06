import gevent
from gevent import monkey; monkey.patch_all()
import requests
from lxml import etree
import datetime
import hashlib
import pymongo

from utils.redis_tool import Rdis_Queue
import re
from bs4 import BeautifulSoup
from utils.zb_storage_setting import StorageSetting
from utils.cpca import *

class GovBuy(object):
    '''广东政府采购网'''
    def __init__(self):
        name = 'guangdong_gdgpo_gov_cn'
        self.coll = StorageSetting(name)
        self.collection = self.coll.find_collection
        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'http://www.gdgpo.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.gdgpo.gov.cn',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }
        self.cookies = {
            'PortalCookie': '4lfPF0Vz1uXun2bBbApFP_N0iCpCdNJyhZ-gQ9R8pyn2bQ0bwhpH^!1287054370',
            'ManageSystemCookie': 'cQ7PF0Ztj6damGs-8Ufh8J1VAmISzBBuzlw406aLTRkYXu09fgWO^!-1871255990',
        }
        self.session = requests.session()


        self.rq = Rdis_Queue(host='localhost', dblist='guangdong_list1', dbset='guangdong_set1')


    def is_running(self):
        is_runing = True
        if self.rq.r_len() == 0 and len (self.rq.rset_info()) > 0:
            return False
        else:
            return is_runing

    def hash_to_md5(self, sign_str):
        m = hashlib.md5()
        # print(sign_str)
        sign_str = sign_str.encode('utf-8')

        m.update(sign_str)
        sign = m.hexdigest()
        return sign

    def now_time(self):
        time_stamp = datetime.datetime.now()
        return time_stamp.strftime('%Y-%m-%d %H:%M:%S')

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

    def save_to_mongo(self,result_dic):
        self.coll.saves(result_dic)
        self.is_running()

    def load_get(self,page):
        try:
            data = [
                ('channelCode', '-1'),
                ('issueOrgan', ''),
                ('operateDateFrom', ''),
                ('operateDateTo', ''),
                ('performOrgName', ''),
                ('pointPageIndexId', '1'),
                ('pointPageIndexId', '2'),
                ('purchaserOrgName', ''),
                ('regionIds', ''),
                ('sitewebId', '-1'),
                ('sitewebName', ''),
                ('stockIndexName', ''),
                ('stockNum', ''),
                ('stockTypes', ''),
                ('title', ''),
                ('pageIndex', str(page)),
                ('pageSize', '15'),
            ]
            url = 'http://www.gdgpo.gov.cn/queryMoreInfoList.do'
            response = self.session.post(url=url, headers=self.headers,data=data).content.decode('utf-8')
            selector = etree.HTML(response)
            url_li = selector.xpath('//*[@id="contianer"]/div[3]/div[2]/div[3]/ul/li/a/@href')
        except:
            print('load_post error')
        else:
            for url in url_li:
                url = 'http://www.gdgpo.gov.cn'+ url
                if not self.rq.in_rset(url):
                    # print(url)
            #         self.rq.add_to_rset(url)
            #         self.rq.pull_to_rlist(url)

                    self.load_get_html(url)

            print('第{}页'.format(page))

    def load_get_html(self,url):
        try:
            response = self.session.get(url=url, headers=self.headers, cookies=self.cookies).content.decode('utf-8')
            selector = etree.HTML(response)
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            try:

                title = selector.xpath('//div[@class="zw_c_cont"]/div[1]/text()')
                if title != []:
                    title = title[0]
                    try:
                        status = re.search(r'[\u4e00-\u9fa5]{2}公告$', title).group()
                    except:
                        status = '公告'
                else:
                    title = None
                    status = '公告'
                if title == None:
                    return
                # print(title)
                _id = self.hash_to_md5(title)

                publish_date = selector.xpath('//div[@class="zw_c_cont"]/div[2]/p/span//text()')
                if publish_date != []:
                    try:
                        publish_date = re.search(r'(\d+\-\d+\-\d+)',''.join(publish_date)).group()
                    except:
                        publish_date = None
                else:
                    publish_date = None

                soup = BeautifulSoup(response)
                content_html = soup.find(class_='zw_c_cont')
                if content_html == None:
                    raise EOFError
                # print(content_html)
                # print(content)
                area_name =self.get_area('广东', title)
                source = 'http://www.gdgpo.gov.cn/'
            except Exception as e:
                print('页面数据存不存在:{}'.format(e))
                print('error_url={}'.format(url))
            else:
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
                retult_dict['zh_name'] = '广东省政府采购网 '
                retult_dict['en_name'] = 'Guangdong Government Procurement'

                # print(retult_dict)
                #
                # print('列表长度为={}'.format(self.rq.r_len()))
                #
                self.save_to_mongo(retult_dict)


    def run(self):
        # threading.Thread(target=self.init).start()
        task_li = [
                # {'all_page': 60958},
                {'all_page': 5},
            ]
        count = 3
        for task in task_li:
            for page in range(1,task['all_page'] + 1,count):


                spawns = [gevent.spawn(self.load_get, page + i) for i in range(count)]
                gevent.joinall(spawns)

                # self.load_get(page)

    def main(self):
        self.run()


if __name__ == '__main__':
    gb = GovBuy()
    gb.main()
