# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config
import re
from urllib.parse import quote
import requests
from datetime import datetime

# 中国海关政府采购
# hgcg_list = [5, 20, 'hgcg_list_url', 'hgcg_customs_gov_cn']
# http://hgcg.customs.gov.cn

pagenum = config.hgcg_list[0]  # 翻页深度
threads = config.hgcg_list[1]  # 线程数
dbname = config.hgcg_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.hgcg_list[3])

session = requests.session()
header = {
    'Host': 'hgcg.customs.gov.cn',
    'Origin': 'http://hgcg.customs.gov.cn',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
}


# 列表链接构造
def list_url():
    l1 = ['http://hgcg.customs.gov.cn/hgcg/cggg/004001/MoreInfo.aspx?CategoryNum=004001' + '#' + '61',
          'http://hgcg.customs.gov.cn/hgcg/cggg/004002/MoreInfo.aspx?CategoryNum=004002' + '#' + '15',
          'http://hgcg.customs.gov.cn/hgcg/cggg/004003/MoreInfo.aspx?CategoryNum=004003' + '#' + '40',
          'http://hgcg.customs.gov.cn/hgcg/cggg/004004/MoreInfo.aspx?CategoryNum=004004' + '#' + '34',
          ]
    return l1


# 列表解析(详情url)
def list_parse():
    list_url = save.pop(name=dbname)
    if list_url is None:
        return
    total = int(list_url.split('#')[-1])
    list_url = list_url.split('#')[0]
    response = session.get(list_url, headers=header).text
    if response is None:
        return
    html = etree.HTML(response)
    Urls = html.xpath('//tr[@valign="top"]/td[@align="left"]/a/@href')
    # print('--------------------------------------------')
    for Url in Urls:
        # pass
        # print('http://hgcg.customs.gov.cn' + Url)
        detail_parse('http://hgcg.customs.gov.cn' + Url)
    res = response
    for page in range(2, total):
        try:
            html = etree.HTML(res)
            data = '__VIEWSTATE={}&__VIEWSTATEGENERATOR={}&__EVENTTARGET={}&__EVENTARGUMENT={}'.format(
                quote(html.xpath('//input[@id="__VIEWSTATE"]/@value')[0]),
                quote(html.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')[0]),
                quote('MoreInfoList1$Pager'),
                str(page),
            )
            # proxy = {'http': 'http://127.0.0.1:8080'}
            res = session.post(list_url, data=data,headers=header).text
            html = etree.HTML(res)
            Urls = html.xpath('//tr[@valign="top"]/td[@align="left"]/a/@href')
            # print('--------------------------------------------')
            for Url in Urls:
                detail_parse('http://hgcg.customs.gov.cn' + Url)
        except:
            pass


# 详情解析
def detail_parse(url):
    item = {}
    if url is None:
        return
    response = request.get(url, type='gb2312')
    if response is None:
        return
    Html = etree.HTML(response)
    titles = Html.xpath('//td[@id="tdTitle"]//b/text()')
    item['title'] = str(titles[0]).strip() if len(titles) != 0 else None
    if item['title'] is None:
        return
    item['area_name'] = '全国'
    item['source'] = 'http://hgcg.customs.gov.cn'

    date = re.findall('([0-9]{4,5}/[0-9]{1,2}/[0-9]{1,2})', response)
    item['publish_date'] = date[0] if len(date) != 0 else ''
    item['detail_url'] = url
    item['create_time'] = datetime.now()
    item['zh_name'] = '中国海关政府采购网'
    item['en_name'] = 'China Customs Government Procurement'
    # 详情解析
    div_html = Html.xpath('//table[@id="tblInfo"]')
    content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                 method="html").decode('utf-8')
    item['content_html'] = content_html
    html1 = etree.HTML(content_html)
    # 状态
    # states = Html.xpath('//div[@class="location"]/a/text()')
    if '004001' in url:
        item['status'] = '招标公告'
    elif '004002' in url:
        item['status'] = '变更公告'
    elif '004003' in url:
        item['status'] = '中标公告'
    else:
        item['status'] = '成交公告'
    # item['status'] = str(states[-1]).strip() if len(states) != 0 else None
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
