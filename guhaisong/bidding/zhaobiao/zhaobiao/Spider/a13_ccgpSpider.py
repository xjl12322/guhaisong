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
# 长春政府采购中心
# ccgp_list = [5, 20, 'ccgp_list_url', 'ccgp_com_cn']
# http://www.ccgp.com.cn

pagenum = config.ccgp_com_list[0]  # 翻页深度
threads = config.ccgp_com_list[1]  # 线程数
dbname = config.ccgp_com_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.ccgp_com_list[3])


# 列表链接构造
def list_url():
    api = 'http://www.ccgp.com.cn/ccgp/list/stocklist.jsp?toPage={}&type=&bulletin_name='
    l1 = [api.format(i) for i in range(0, pagenum)]
    # l1 = [api.format(i) for i in range(0, 2)]
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
                urls = html.xpath('//tr[@height="22"]/td/a[@target="_blank"]/@href')
                # print(urls)
                for url in urls:
                    title = ''.join(html.xpath(
                        '//a[@href="{}"]/text()'.format(url)))
                    # print(title)
                    date = ''.join(html.xpath('//a[@href="{}"]/../following-sibling::td[last()]/text()'.format(url)))
                    # print('//a[@href="{}"]/../following-sibling::td[last()]/text()'.format(url))
                    if title != '' and date != '':
                        item = 'http://www.ccgp.com.cn/ccgp/list' + str(url).replace('./',
                                                                                     '/') + '**' + title + '**' + date
                        detail_parse(item)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        date = url.split('**')[2]
        title = url.split('**')[1]
        url = url.split('**')[0]
        item = {}
        response = request.get(url, type='GB2312')
        # print(response)
        if response is not None:
            Html = etree.HTML(response)
            item['title'] = title
            item['area_name'] = '长春'
            item['source'] = 'http://www.ccgp.com.cn'
            item['publish_date'] = date
            item['detail_url'] = url
            item['create_time'] =datetime.now()
            item['zh_name'] = '长春市政府采购'
            item['en_name'] = 'Changchun City Government Procurement'
            div_html = Html.xpath('//td[@align="center"]')
            if len(div_html)==0:
                div_html = Html.xpath('//div[@align="center"]')
            if len(div_html) != 0:
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                if 'serv_type_id=1' in url:
                    item['status'] = '公开招标'
                elif 'serv_type_id=3' in url:
                    item['status'] = '询价采购'
                elif 'serv_type_id=5' in url:
                    item['status'] = '单一来源'
                elif 'serv_type_id=4' in url:
                    item['status'] = '竞争性谈判'
                elif 'serv_type_id=2' in url:
                    item['status'] = '邀请招标'
                else:
                    item['status'] = '其他采购'
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
