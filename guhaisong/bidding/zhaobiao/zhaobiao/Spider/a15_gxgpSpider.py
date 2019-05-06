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
# 广西壮族自治区政府采购
# gxgp_list = [5, 20, 'gxgp_list_url', 'gxgp_gov_cn']
# http://www.gxgp.gov.cn

pagenum = config.gxgp_list[0]  # 翻页深度
threads = config.gxgp_list[1]  # 线程数
dbname = config.gxgp_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.gxgp_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.gxgp.gov.cn/ygswz/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l2 = ['http://www.gxgp.gov.cn/cggkzb/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l3 = ['http://www.gxgp.gov.cn/cgjz/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l4 = ['http://www.gxgp.gov.cn/cgjzxcs/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l5 = ['http://www.gxgp.gov.cn/cgdyly/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l6 = ['http://www.gxgp.gov.cn/cgxjcg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l7 = ['http://www.gxgp.gov.cn/zbxjcg/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l8 = ['http://www.gxgp.gov.cn/zbdyly/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l9 = ['http://www.gxgp.gov.cn/zbcgjzxcs/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l10 = ['http://www.gxgp.gov.cn/zbjz/index_{}.htm'.format(i) for i in range(1, pagenum)]
    l11 = ['http://www.gxgp.gov.cn/zbgkzb/index_{}.htm'.format(i) for i in range(1, pagenum)]
    return l1 + l2 + l3 + l4 + l5 + l6+l7+l8+l9+l10+l11
    # return l5


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
            titles = Html.xpath('//div[@class="ctitle ctitle1"]/text()')
            item['title'] = titles[0] if len(titles) != 0 else None
            if item['title'] is not None:
                item['area_name'] = '广西壮族自治区'
                item['source'] = 'http://www.gxgp.gov.cn'
                date = re.findall('发布日期：(\d\d\d\d-\d\d-\d\d)', response)
                item['publish_date'] = date[0] if len(date) != 0 else '未公布'

                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '广西壮族自治区政府采购中心'
                item['en_name'] = 'Guangxi Government Procurement Center'

                div_html = Html.xpath('//div[@class="page_row"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                if 'ygswz' in url:
                    item['status'] = '预公告'
                elif 'cgxjcg' in url or 'cggkzb' in url or 'cgjz' in url or 'cgjzxcs' in url or 'cgdyly' in url:
                    item['status'] = '采购公告'
                else:
                    item['status'] = '中标公告'

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
