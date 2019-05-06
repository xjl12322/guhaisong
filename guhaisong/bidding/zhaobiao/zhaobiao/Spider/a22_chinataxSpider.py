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
# 国家税务总局
# chinatax_list = [5, 20, 'chinatax_list_url', 'chinatax_gov_cn']
# http://www.chinatax.gov.cn

pagenum = config.chinatax_list[0]  # 翻页深度
threads = config.chinatax_list[1]  # 线程数
dbname = config.chinatax_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.chinatax_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.chinatax.gov.cn/n810214/n810621/n810668/index.html',
          'http://www.chinatax.gov.cn/n810214/n810621/n810673/index.html',
          'http://www.chinatax.gov.cn/n810214/n810621/n2217729/index.html',
          'http://www.chinatax.gov.cn/n810214/n810621/n3014142/index.html',
          ]
    l2 = ['http://www.chinatax.gov.cn/n810214/n810621/n810668/index_831221_{}.html'.format(i) for i in range(1, pagenum)]
    l3 = ['http://www.chinatax.gov.cn/n810214/n810621/n810673/index_831221_{}.html'.format(i) for i in range(1, pagenum)]
    l4 = ['http://www.chinatax.gov.cn/n810214/n810621/n2217729/index_831221_{}.html'.format(i) for i in range(1, pagenum)]
    l5 = ['http://www.chinatax.gov.cn/n810214/n810621/n3014142/index_831221_{}.html'.format(i) for i in range(1, pagenum)]
    return l1 + l2 + l3 + l4 + l5
    # return l1+l2


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
        urls = html.xpath('//dd/a[contains(@href,"content.html")]/@href')
        for url in urls:
            detail_parse('http://www.chinatax.gov.cn/'+str(url).replace('../',''))


# 详情解析
def detail_parse(url):
    item = {}
    if url is None:
        return
    response = request.get(url, type='utf-8')
    if response is None:
        return
    Html = etree.HTML(response)
    titles = Html.xpath('//li[@class="sv_texth1"]/text()')
    item['title'] = str(titles[0]).strip() if len(titles) != 0 else None
    if item['title'] is None:
        return
    item['area_name'] = '全国'
    item['source'] = 'http://www.chinatax.gov.cn'

    date = re.findall('(\d\d\d\d年\d\d月\d\d日)',response)
    item['publish_date'] = date[0] if len(date)!=0 else ''
    item['detail_url'] = url
    item['create_time'] = datetime.now()
    item['zh_name'] = '国家税务总局'
    item['en_name'] = 'State Administration of Taxation'
    # 详情解析
    div_html = Html.xpath('//ul[@class="sv_textcon"]')
    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                 method="html").decode('utf-8')
    item['content_html'] = content_html
    html1 = etree.HTML(content_html)
    # 状态
    states = Html.xpath('//div[@class="location"]/a/text()')
    # if 'cgzbgg' in url:
    #     item['status'] = '中标公告'
    # else:
    #     item['status'] = '采购公告'
    item['status'] = str(states[-1]).strip() if len(states) != 0 else None
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
