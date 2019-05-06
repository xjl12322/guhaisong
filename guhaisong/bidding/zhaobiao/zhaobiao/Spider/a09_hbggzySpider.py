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
# 湖北公共资源交易中心
# hbggzy_list = [5, 20, 'hbggzy_list_url', 'hbggzy_gov_cn']
# http://www.hbggzy.cn

pagenum = config.hbggzy_list[0]  # 翻页深度
threads = config.hbggzy_list[1]  # 线程数
dbname = config.hbggzy_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.hbggzy_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.hbggzy.cn/jydt/003001/003001001/{}.html'.format(i) for i in range(1, pagenum)]
    l2 = ['http://www.hbggzy.cn/jydt/003001/003001002/{}.html'.format(i) for i in range(1, pagenum)]
    l3 = ['http://www.hbggzy.cn/jydt/003001/003001003/{}.html'.format(i) for i in range(1, pagenum)]
    l4 = ['http://www.hbggzy.cn/jydt/003001/003001004/{}.html'.format(i) for i in range(1, pagenum)]
    l5 = ['http://www.hbggzy.cn/jydt/003001/003001005/{}.html'.format(i) for i in range(1, pagenum)]
    return l1 + l2 + l3 + l4+l5
    # return l1


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//ul[@class="ewb-news-items"]/li/a/@href')
                for url in urls:
                    detail_parse('http://www.hbggzy.cn' + url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:

        item = {}
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//h6[@class="news-article-tt"]/text()')
            if len(titles) > 0:
                item['title'] = str(titles[0]).strip()
                item['area_name'] = '湖北'
                item['source'] = 'http://www.hbggzy.cn'
                date = re.findall('发稿时间 ：(\d\d\d\d-\d\d-\d\d)', response)
                item['publish_date'] = str(date[0]).strip() if len(date) > 0 else None

                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '湖北省公共资源交易网'
                item['en_name'] = 'Hubei Province Government Procurement'
                div_html = Html.xpath('//div[@class="ewb-row"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                states = Html.xpath('//div[@class="ewb-route"]/span[last()]/text()')
                item['status'] = states[-1] if len(states) != 0 else None
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
