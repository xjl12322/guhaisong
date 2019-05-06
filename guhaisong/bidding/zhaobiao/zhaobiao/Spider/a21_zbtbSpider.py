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
# 全国招标信息网
# zbtb_list = [5, 20, 'zbtb_list_url', 'zbtb_com_cn']
# http://zbtb.com.cn

pagenum = config.zbtb_list[0]  # 翻页深度
threads = config.zbtb_list[1]  # 线程数
dbname = config.zbtb_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.zbtb_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://zbtb.com.cn/caigou/gonggao-38046--{}.html'.format(i) for i in range(1, pagenum)] # 2857
    l2 = ['http://zbtb.com.cn/caigou/gongshi-38047--{}.html'.format(i) for i in range(1, pagenum)]
    l3 = ['http://zbtb.com.cn/caigou/yugao-38048--{}.html'.format(i) for i in range(1, pagenum)]
    l4 = ['http://zbtb.com.cn/caigou/mianfei-38049--{}.html'.format(i) for i in range(1, pagenum)]
    l5 = ['http://zbtb.com.cn/caigou/huiyuan-38093--{}.html'.format(i) for i in range(1, pagenum)]
    l6 = ['http://zbtb.com.cn/caigou/xixun-38094--{}.html'.format(i) for i in range(1, pagenum)]
    return l1+l2


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is None:
            break
        response = request.get(list_url)
        if response is None:
            return   # http://zbtb.com.cn/caigou/zhaobiao-c1762379.html
        html = etree.HTML(response)
        urls = html.xpath('//td[@class="td_left"]/a/@href')
        for url in urls:
            area_names = html.xpath('//a[@href="{}"]/../preceding-sibling::td//text()'.format(url))
            area_name = area_names[0] if len(area_names)!=0 else '全国'
            detail_parse(url+'**'+area_name)


# 详情解析
def detail_parse(url):
    item = {}
    if url is None:
        return
    area_name = str(url).split('**')[-1]
    url = str(url).split('**')[0]
    response = request.get(url, type='utf-8')
    if response is None:
        return
    Html = etree.HTML(response)
    titles = Html.xpath('//div[@class="xq_title"]/h1/text()')
    item['title'] = str(titles[0]).strip() if len(titles) != 0 else None
    if item['title'] is None:
        return
    item['area_name'] = area_name
    item['source'] = 'http://zbtb.com.cn'

    # date = Html.xpath('//td[contains(text(),"发布时间")]//text()')
    date = re.findall('信息时间：(\d\d\d\d-\d\d-\d\d)',response)
    item['publish_date'] = date[0] if len(date)!=0 else ''
    item['detail_url'] = url
    item['create_time'] = datetime.now()
    item['zh_name'] = '全国招标信息网'
    item['en_name'] = 'Bidding Information Network'
    # 详情解析
    div_html = Html.xpath('//div[@class="zhaobiaoxq"]')
    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                 method="html").decode('utf-8')
    item['content_html'] = str(content_html).replace('class="bottom_pay"','class="bottom_pay" style="display:none"').replace('class="xq_ul"','class="xq_ul" style="display:none"')
    html1 = etree.HTML(content_html)
    # 状态
    states = Html.xpath('//a[contains(text(),"正文")]/preceding-sibling::a[1]/text()')
    # if 'cgzbgg' in url:
    #     item['status'] = '中标公告'
    # else:
    #     item['status'] = '采购公告'
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
