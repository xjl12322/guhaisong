# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import re, time
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
from datetime import datetime

# import config
import config

# 网址 http://www.cqzb.gov.cn/


pagenum = config.cqzb_list[0]  # 翻页深度
threads = config.cqzb_list[1]  # 线程数
dbname = config.cqzb_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.cqzb_list[3])


# 列表链接构造
def list_url():
    zhaobs = ['http://www.cqzb.gov.cn/class-5-1({}).aspx'.format(i) for i in range(1, pagenum)]
    zhongbs = ['http://www.cqzb.gov.cn/class-5-45({}).aspx'.format(i) for i in range(1, pagenum)]
    return zhaobs + zhongbs


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//div[@class="ztb_list_right"]/ul/li/a/@href')
                for url in urls:
                    detail_parse('http://www.cqzb.gov.cn/' + url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url)
        if response is not None:
            titles = re.findall('\$\("#tith1"\)\.html\("(.*?)"\);', response)
            title = str(titles[1]).replace('  ', '').replace('\r', '').replace('\n', '') if len(titles) == 2 else None
            if title is not None:
                if '招标' in title:
                    item['status'] = '招标公告'
                else:
                    item['status'] = '中标公告'
                item['title'] = title
                item['area_name'] = '重庆'
                item['source'] = 'http://www.cqzb.gov.cn'
                date = re.findall('发布时间： (\d\d\d\d-\d\d-\d\d)', response)
                item['publish_date'] = date[0] if len(date) > 0 else None
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '重庆市招标投标综合网'
                item['en_name'] = 'Chongqing Bidding Comprehensive Network'
                selector = etree.HTML(response)
                div_html = selector.xpath('//div[@class="ztb_con_exp"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
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
