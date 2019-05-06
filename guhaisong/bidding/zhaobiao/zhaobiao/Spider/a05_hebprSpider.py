# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time, re
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
from datetime import datetime

import config

# 网址 http://www.hebpr.cn/


pagenum = config.hebpr_list[0]  # 翻页深度
threads = config.hebpr_list[1]  # 线程数
dbname = config.hebpr_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.hebpr_list[3])


# 列表链接构造
def list_url():
    zbgg = ['http://www.hebpr.cn/hbjyzx/002/002009/002009001/{}.html'.format(i) for i in range(1, pagenum)]
    return zbgg


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//a[@class="frame-con-link clearfix"]/@href')
                for url in urls:
                    detail_parse('http://www.hebpr.cn' + url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//h1[@class="show-title"]/text()')
            if len(titles) > 0:
                item['title'] = str(titles[0]).strip()
                item['area_name'] = '河北'
                item['source'] = 'http://www.hebpr.cn'
                # date = re.findall('发布日期：(\d\d\d\d-\d\d-\d\d)', response)
                item['publish_date'] = ''
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '河北省政务服务管理办公室'
                item['en_name'] = 'Hebei Province Public resource'

                div_html = Html.xpath('//div[@class="show-con infoContent"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                states = Html.xpath('//div[@class="bread-route"]/a[last()]/text()')
                item['status'] = states[0] if len(states) != 0 else None
                Save.push(item=item, key=url)


def run():
    # 判断是否存在列表队列
    if not save.judge(dbname):
        # 构造列表页
        for url in list_url():
            save.push(name=dbname, value=url)
    # 获取详情链接
    spawns = [gevent.spawn(list_parse, ) for _ in range(threads)]
    gevent.joinall(spawns)


if __name__ == '__main__':
    run()
