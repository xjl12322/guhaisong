# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config
import re

from datetime import datetime
# 北京政府采购中心
# bgpc_gov_list = [5, 20, 'bgpc_gov_list_url', 'bgpc_gov_cn']
# http://www.bgpc.gov.cn

pagenum = config.bgpc_gov_list[0]  # 翻页深度
threads = config.bgpc_gov_list[1]  # 线程数
dbname = config.bgpc_gov_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.bgpc_gov_list[3])


# 列表链接构造
def list_url():
    api = 'http://www.bgpc.gov.cn/defaults/news/news/page/{}/tid/9'
    l1 = [api.format(i) for i in range(0, pagenum)]
    # l1 = [api.format(i) for i in range(1, 2)]
    return l1
    # return l2


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                # print(response)
                html = etree.HTML(response)
                urls = html.xpath('//div[@class="content-right-content-center"]//a/@href')
                # print(urls)
                for url in urls:
                    # print('http://www.jlszfcg.gov.cn' + url)
                    detail_parse('http://www.bgpc.gov.cn' + url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url,type='utf-8')
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="content-right-details-top"]/span/text()')
            if len(titles) > 0:
                if str(titles[0]).strip() != '':
                    item['title'] = str(titles[0]).strip()
                    item['area_name'] = '北京'
                    item['source'] = 'http://www.bgpc.gov.cn'

                    date = re.findall('发布时间：(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)', response)
                    item['publish_date'] = str(date[0]).strip() if len(date) > 0 else None

                    item['detail_url'] = url
                    item['create_time'] = datetime.now()
                    item['zh_name'] = '北京市政府采购中心'
                    item['en_name'] = 'Beijing Government Procurement Center'

                    div_html = Html.xpath('//div[@class="content-right-details-content"]')
                    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                                 method="html").decode('utf-8')
                    item['content_html'] = content_html
                    html1 = etree.HTML(content_html)
                    states = Html.xpath('//div[@class="content-right-content-top"]//a/text()')
                    item['status'] = states[-1] if len(states) != 0 else None
                    Save.push(item=item, key=url)


def run():
    # 判断是否存在列表队列
    if not save.judge(dbname):
        # 构造列表页
        for url in list_url():
            save.push(name=dbname, value=url)
    # 获取详情链接
    # list_parse()
    spawns = [gevent.spawn(list_parse, ) for _ in range(threads)]
    gevent.joinall(spawns)


if __name__ == '__main__':
    run()
