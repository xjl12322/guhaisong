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
# 海南省公共资源交易平台
# hainan_list = [5, 20, 'hainan_list_url', 'hainan_gov_cn']
# http://zw.hainan.gov.cn

pagenum = config.hainan_list[0]  # 翻页深度
threads = config.hainan_list[1]  # 线程数
dbname = config.hainan_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.hainan_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://zw.hainan.gov.cn/ggzy/ggzy/cgzbgg/index_{}.jhtml'.format(i) for i in range(1, pagenum)]
    l2 = ['http://zw.hainan.gov.cn/ggzy/ggzy/cggg/index_{}.jhtml'.format(i) for i in range(1, pagenum)]
    return l1 + l2
    # return l5


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is None:
            break
        response = request.get(list_url)
        if response is None:
            return
        html = etree.HTML(response)
        urls = html.xpath('//td[@align="left"]/a/@href')
        for url in urls:
            dates = html.xpath('//a[@href="{}"]/../../td[last()]/text()'.format(url))
            date = dates[0] if len(dates)!=0 else None
            detail_parse(url+'**'+date)


# 详情解析
def detail_parse(url):
    item = {}
    if url is None:
        return
    date = str(url).split('**')[-1]
    url = str(url).split('**')[0]
    response = request.get(url, type='utf-8')
    if response is None:
        return
    Html = etree.HTML(response)
    titles = Html.xpath('//div[@class="newsTex"]/h1/text()')
    item['title'] = str(titles[0]).strip() if len(titles) != 0 else None
    if item['title'] is None:
        return
    item['area_name'] = '海南省'
    item['source'] = 'http://zw.hainan.gov.cn'

    # date = Html.xpath('//td[contains(text(),"发布时间")]//text()')
    item['publish_date'] = date
    item['detail_url'] = url
    item['create_time'] = datetime.now()
    item['zh_name'] = '海南省人民政府政务服务中心'
    item['en_name'] = 'Hainan Province Government Service Center'
    # 详情解析
    div_html = Html.xpath('//div[@class="newsTex"]')
    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                 method="html").decode('utf-8')
    item['content_html'] = content_html
    html1 = etree.HTML(content_html)
    # 状态
    # states = Html.xpath('//td[contains(text(),"当前位置")]/span/a[last()]/text()')
    if 'cgzbgg' in url:
        item['status'] = '中标公告'
    else:
        item['status'] = '采购公告'
    # item['status'] = str(states[0]).strip() if len(states) != 0 else None
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
