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
# 吉林省政府采购中心
# jlszfcg_list = [5, 20, 'jlszfcg_list_url', 'jlszfcg_gov_cn']
# http://www.jlszfcg.gov.cn

pagenum = config.jlszfcg_list[0]  # 翻页深度
threads = config.jlszfcg_list[1]  # 线程数
dbname = config.jlszfcg_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.jlszfcg_list[3])


# 列表链接构造
def list_url():
    api = 'http://www.jlszfcg.gov.cn/jilin/zbxxController.form?bidWay='
    l1 = [api + 'GKZB&declarationType=ZHAOBGG&declarationType=GSGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    l2 = [api + 'YQZB&declarationType=ZHAOBGG&declarationType=GSGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    l3 = [api + 'JZXTP&declarationType=ZHAOBGG&declarationType=GSGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    l4 = [api + 'XJCG&declarationType=ZHAOBGG&declarationType=GSGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    l5 = [api + 'JZXCS&declarationType=ZHAOBGG&declarationType=GSGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    l6 = [api + 'DZJJCG&declarationType=&pageNo={}'.format(i) for i in range(0, pagenum)]
    l7 = [api + 'DYCGLY&declarationType=ZHAOBGG&declarationType=GSGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    l8 = [api + '&declarationType=ZQYJGG&pageNo={}'.format(i) for i in range(0, pagenum)]
    return l1 + l2 + l3 + l4 + l5 + l6 + l7 + l8
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
                urls = html.xpath('//li//a/@href')
                # print(urls)
                for url in urls:
                    # print('http://www.jlszfcg.gov.cn' + url)
                    detail_parse('http://www.jlszfcg.gov.cn' + str(url).replace('../','/'))
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url,type='utf-8')
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="bx_title"]/text()')
            if len(titles) > 0:
                if str(titles[0]).strip() != '':
                    item['title'] = str(titles[0]).strip()
                    item['area_name'] = '吉林'
                    item['source'] = 'http://www.jlszfcg.gov.cn'

                    date = re.findall('发布日期：(\d\d\d\d-\d\d-\d\d)', response)
                    item['publish_date'] = str(date[0]).strip() if len(date) > 0 else None

                    item['detail_url'] = url
                    item['create_time'] = datetime.now()
                    div_html = Html.xpath('//div[@class="con08_b"]')
                    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                                 method="html").decode('utf-8')
                    item['content_html'] = content_html
                    html1 = etree.HTML(content_html)
                    states = re.findall('\(.*?\)',item['title'])
                    item['status'] = str(states[-1]).strip('(').strip(')') if len(states) != 0 else None
                    item['zh_name'] = '吉林省政府采购中心'
                    item['en_name'] = 'Jilin Government procurement center'
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
