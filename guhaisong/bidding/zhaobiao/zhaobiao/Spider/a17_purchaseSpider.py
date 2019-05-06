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
# 南宁市政府集中采购中心
# purchase_list = [5, 20, 'purchase_list_url', 'purchase_gov_cn']
# http://www.purchase.gov.cn

pagenum = config.purchase_list[0]  # 翻页深度
threads = config.purchase_list[1]  # 线程数
dbname = config.purchase_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.purchase_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.purchase.gov.cn//cxqgsgg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l2 = ['http://www.purchase.gov.cn//xqgshfgg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l3 = ['http://www.purchase.gov.cn//sjcggg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l4 = ['http://www.purchase.gov.cn//sjbggg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l5 = ['http://www.purchase.gov.cn//sjzbgs/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l6 = ['http://www.purchase.gov.cn//wsjj/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l7 = ['http://www.purchase.gov.cn//xqcggg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l8 = ['http://www.purchase.gov.cn//xqbggg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l9 = ['http://www.purchase.gov.cn//xqzbgg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    return l1 + l2 + l3 + l4 + l5 + l6 + l7 + l8 + l9
    # return l1


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//div[@class="c1-bline"]//a/@href')
                for url in urls:
                    detail_parse(url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url, type='gb2312')
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="W980 center PaddingTop10"]/div[1]/text()')
            item['title'] = titles[0] if len(titles) != 0 else None
            if item['title'] is not None:
                item['area_name'] = '南宁'
                item['source'] = 'http://www.purchase.gov.cn'
                date = re.findall('发布日期：(\d\d\d\d-\d\d-\d\d)', response)
                item['publish_date'] = date[0] if len(date) != 0 else '未公布'

                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '南宁政府集中采购中心'
                item['en_name'] = 'Nanning Government Procurement Center'

                div_html = Html.xpath('//div[@class="W980 center PaddingTop10"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                if 'cxqgsgg' in url:
                    item['status'] = '需求公示公告'
                elif 'xqgshfgg' in url:
                    item['status'] = '需求公示回复公告'
                elif 'sjcggg' in url or 'xqcggg' in url:
                    item['status'] = '采购公告'
                elif 'sjbggg' in url or 'xqbggg' in url:
                    item['status'] = '变更公告'
                elif 'sjzbgs' in url or 'xqzbgg' in url:
                    item['status'] = '中标公告'
                else:
                    item['status'] = '办公电器公告'

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
