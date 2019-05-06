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

# 长沙公共资源交易监管网
# csggzy_list = [5, 20, 'csggzy_list_url', 'csggzy_gov_cn']
# https://csggzy.gov.cn

pagenum = config.csggzy_list[0]  # 翻页深度
threads = config.csggzy_list[1]  # 线程数
dbname = config.csggzy_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.csggzy_list[3])


# 列表链接构造
def list_url():
    l1 = ['https://csggzy.gov.cn/NoticeFile.aspx/Index/{}?type=undefined&Ptype=政府采购&Sm2=全部&Sm=政府采购'.format(i) for i in
          range(1, pagenum)]
    return l1


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//tr/td/a/@href')
                for url in urls:
                    # print('https://csggzy.gov.cn' + url)
                    detail_parse('https://csggzy.gov.cn' + url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="detail_t"]/h1/text()')
            if len(titles) == 0:
                titles = Html.xpath('//span[@id="title"]/text()')
            if len(titles) == 0:
                titles = Html.xpath('//p[@style="TEXT-ALIGN: center"]/text()')
            if len(titles) == 0:
                titles = Html.xpath('//p[@style="TEXT-ALIGN: right"]/text()')
            if len(titles) == 0:
                titles = Html.xpath('//span[@style="FONT-SIZE: 20px"]/strong/text()')
            if len(titles) > 0:
                if str(titles[0]).strip() != '':
                    item['title'] = str(titles[0]).strip()
                    item['area_name'] = '长沙'
                    item['source'] = 'http://csggzy.changsha.gov.cn/'

                    date = re.findall('发布日期：(\d\d\d\d-\d\d-\d\d)', response)
                    item['publish_date'] = str(date[0]).strip() if len(date) > 0 else None

                    item['detail_url'] = url
                    item['create_time'] = datetime.now()
                    div_html = Html.xpath('//div[@class="detail"]')
                    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                                 method="html").decode('utf-8')
                    item['content_html'] = content_html
                    states = Html.xpath('//div[@id="dh"]/a/text()')
                    item['status'] = str(states[-1]).strip() if len(states) != 0 else None
                    item['zh_name'] = '长沙公共资源交易中心'
                    item['en_name'] = 'Changsha Public resource'
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
