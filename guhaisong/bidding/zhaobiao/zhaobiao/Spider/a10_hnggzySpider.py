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
# 河南公共资源交易中心
# hnggzy_list = [5, 20, 'hnggzy_list_url', 'hnggzy_gov_cn']
# http://www.hnggzy.com

pagenum = config.hnggzy_list[0]  # 翻页深度
threads = config.hnggzy_list[1]  # 线程数
dbname = config.hnggzy_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.hnggzy_list[3])


# 列表链接构造
def list_url():
    zbgg = ['http://www.hnggzy.com/hnsggzy/jyxx/002002/002002001/?Paging={}'.format(i) for i in range(1, pagenum)]
    bggg = ['http://www.hnggzy.com/hnsggzy/jyxx/002002/002002002/?Paging={}'.format(i) for i in range(1, pagenum)]
    jggg = ['http://www.hnggzy.com/hnsggzy/jyxx/002002/002002003/?Paging={}'.format(i) for i in range(1, pagenum)]
    qtgg = ['http://www.hnggzy.com/hnsggzy/jyxx/002002/002002004/?Paging={}'.format(i) for i in range(1, pagenum)]
    return zbgg + bggg + jggg + qtgg
    # return qtgg


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                if html is not None:
                    urls = html.xpath('//td[@align="left"]/a[@target="_blank"]/@href')
                    for url in urls:
                        detail_parse('http://www.hnggzy.com'+url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:

        item = {}
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//tr/td[@align="center"]/font/text()')
            if len(titles) > 0:
                item['title'] = str(titles[0]).strip()
                item['area_name'] = '河南'
                item['source'] = 'http://www.hnggzy.com'

                date = re.findall('信息时间：(\d{4,5}/\d{1,2}/\d{1,2})',response)
                item['publish_date'] = str(date[0]).strip() if len(date) > 0 else None

                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '河南省公共资源交易中心'
                item['en_name'] = 'Henan Province Public resource'
                div_html = Html.xpath('//table[@align="center"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                states = Html.xpath('//font[contains(text(),"您现在的位置")]/..//a//text()')
                item['status'] = states[-1] if len(states)!=0 else None
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
