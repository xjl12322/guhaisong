# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time,re
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config
from datetime import datetime
# 网址 http://ggzyjy.dl.gov.cn/


pagenum = config.ggzyjy_list[0]  # 翻页深度
threads = config.ggzyjy_list[1]  # 线程数
dbname = config.ggzyjy_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.ggzyjy_list[3])


# 列表链接构造
def list_url():
    cggg = ['http://ggzyjy.dl.gov.cn/TPFront/jyxx/071002/071002001/?pageing={}'.format(i) for i in range(1, pagenum)]
    cgwjgs = ['http://ggzyjy.dl.gov.cn/TPFront/jyxx/071002/071002002/?pageing={}'.format(i) for i in range(1, pagenum)]
    zbtz = ['http://ggzyjy.dl.gov.cn/TPFront/jyxx/071002/071002003/?pageing={}'.format(i) for i in range(1, pagenum)]
    cghtgs = ['http://ggzyjy.dl.gov.cn/TPFront/jyxx/071002/071002004/?pageing={}'.format(i) for i in range(1, pagenum)]
    dyly = ['http://ggzyjy.dl.gov.cn/TPFrontNew/jyxx/071002/071002005/?pageing={}'.format(i) for i in range(1, pagenum)]
    return cggg + cgwjgs + zbtz + cghtgs + dyly


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//tr[@class="ewb-trade-tr"]/td/a/@href')
                for url in urls:
                    detail_parse('http://ggzyjy.dl.gov.cn'+url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="ewb-container"]/h2/text()')
            if len(titles) > 0:
                item['title'] = titles[0]
                item['area_name'] = '大连'
                item['source'] = 'http://ggzyjy.dl.gov.cn'

                date = re.findall('信息时间：(\d\d\d\d-\d\d-\d\d)',response)
                item['publish_date'] = str(date[0]) if len(date) > 0 else None
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '大连市公共资源交易平台'
                item['en_name'] = 'Dalian City Public resource'

                div_html = Html.xpath('//div[@class="article-content"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1= etree.HTML(content_html)
                if '071002001' in url:
                    item['status'] = '采购公告'
                elif '071002002' in url:
                    item['status'] = '采购文件公示'
                elif '071002003' in url:
                    item['status'] = '中标通知'
                elif '071002004' in url:
                    item['status'] = '采购合同公示'
                else:
                    item['status'] = '单一来源'
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
