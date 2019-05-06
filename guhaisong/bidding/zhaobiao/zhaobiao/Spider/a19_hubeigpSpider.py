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
# 湖北政府采购中心
# hubeigp_list = [5, 20, 'hubeigp_list_url', 'hubeigp_gov_cn']
# http://www.hubeigp.gov.cn

pagenum = config.hubeigp_list[0]  # 翻页深度
threads = config.hubeigp_list[1]  # 线程数
dbname = config.hubeigp_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.hubeigp_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.hubeigp.gov.cn/hbscgzx/139295/139299/d6d12652-{}.html'.format(i) for i in
          range(1, pagenum)]
    l2 = ['http://www.hubeigp.gov.cn/hbscgzx/139295/139315/a6618415-{}.html'.format(i) for i in
          range(1, pagenum)]
    l3 = ['http://www.hubeigp.gov.cn/hbscgzx/139295/139303/7889ebc8-{}.html'.format(i) for i in
          range(1, pagenum)]
    l4 = ['http://www.hubeigp.gov.cn/hbscgzx/139295/139323/6f7710e8-{}.html'.format(i) for i in
          range(1, pagenum)]
    l5 = ['http://www.hubeigp.gov.cn/hbscgzx/139295/139311/9d912736-{}.html'.format(i) for i in
          range(1, pagenum)]
    return l1 + l2 + l3 + l4 + l5
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
        urls = html.xpath('//td[@class="linebg"]/a/@href')
        for url in urls:
            detail_parse('http://www.hubeigp.gov.cn' + url)


# 详情解析
def detail_parse(url):
    item = {}
    if url is None:
        return
    response = request.get(url, type='utf-8')
    if response is None:
        return
    Html = etree.HTML(response)
    titles = Html.xpath('//div[@class="title2"]/text()')
    item['title'] = str(titles[0]).strip() if len(titles) != 0 else None
    if item['title'] is None:
        return
    item['area_name'] = '湖北'
    item['source'] = 'http://www.hubeigp.gov.cn'

    date = Html.xpath('//td[contains(text(),"发布时间")]//text()')
    item['publish_date'] = str(date[0]).strip('发布时间：') if len(date) != 0 else '未公布'
    item['detail_url'] = url
    item['create_time'] = datetime.now()
    item['zh_name'] = '湖北省政府采购中心'
    item['en_name'] = 'Hubei Government Procurement Center'
    # 详情解析
    div_html = Html.xpath('//td[@class="h2"]')
    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                 method="html").decode('utf-8')
    item['content_html'] = content_html
    html1 = etree.HTML(content_html)
    # 状态
    states = Html.xpath('//td[contains(text(),"当前位置")]/span/a[last()]/text()')
    item['status'] = str(states[0]).strip() if len(states) != 0 else None
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
