
import requests
import json

import asyncio
import aiohttp
from six.moves import queue
from lxml import etree
from bs4 import BeautifulSoup
import re
import datetime
import pymongo
from utils.cpca import *
from utils.zb_storage_setting import StorageSetting

_page_response_queue = queue.Queue()


# 限制并发数为5个
semaphore = asyncio.Semaphore(1)


name = 'shenyang_ccgp-shenyang_gov_cn'
coll = StorageSetting(name)
collection = coll.find_collection

headers = {
    'Origin': 'http://www.ccgp-shenyang.gov.cn',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh,zh-CN;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'Referer': 'http://www.ccgp-shenyang.gov.cn/sygpimp/portalindex.do?method=goInfo^&linkId=cggg',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
}


def now_time():
    time_stamp = datetime.datetime.now()
    return time_stamp.strftime('%Y-%m-%d %H:%M:%S')

def save_to_mongo(result_dic):
    coll.saves(result_dic)

def get_area(pro, strs):
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

async def get_data(row):
    info_id = row['info_id']
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            url = 'http://www.ccgp-shenyang.gov.cn/sygpimp/portalsys/portal.do?method=pubinfoView&&info_id='+info_id+'&t_k=null'
            async with session.get(url, headers=headers) as html:
                retult_dict = dict()

                response = await html.text()
                # print(response)
                selector = etree.HTML(response)


                title = row['title']
                # print(title)
                # print(content)
                publish_date = row['creation_time']
                # print(publish_date)

                soup = BeautifulSoup(response)
                content_html = soup.find(class_='row')
                # print(content_html)


                _id = row['info_id']

                # print(_id)

                status = row['menu_dl_name']

                area_name = get_area('辽宁', title)
                #
                retult_dict['_id'] = _id
                retult_dict['title'] = title
                retult_dict['status'] = status
                retult_dict['publish_date'] = publish_date
                retult_dict['source'] = 'http://www.ccgp-shenyang.gov.cn'
                retult_dict['area_name'] = area_name

                retult_dict['detail_url'] = url
                retult_dict['content_html'] = str(content_html)
                retult_dict['create_time'] = now_time()
                retult_dict['zh_name'] = '沈阳政府采购网'
                retult_dict['en_name'] = 'Shenyang City Government Procurement'
                # print(retult_dict)
                print(publish_date)
                save_to_mongo(retult_dict)

                return True

async def get_html(current):
    data = {
        'current': current,
        'rowCount': 15,
        'searchPhrase': '',
        'porid': 'cggg'

    }

    async with semaphore:
        async with aiohttp.ClientSession() as session:
            url = 'http://www.ccgp-shenyang.gov.cn/sygpimp/portalsys/portal.do?method=queryHomepageList&t_k=null'
            async with session.post(url, headers=headers,data=data) as html:
                response = await html.json()
                for row in response['rows']:
                    print(row)
                    _page_response_queue.put(row)

loop = asyncio.get_event_loop()
for i in range(1,3):
    tasks = [get_html(i)]

    loop.run_until_complete(asyncio.wait(tasks))
    print('第{}页'.format(i))
    print('queue剩余量：{}'.format(_page_response_queue.qsize()))

    task_data = [get_data(_page_response_queue.get()) for i in range(15)]

    loop.run_until_complete(asyncio.wait(task_data))

loop.close()






