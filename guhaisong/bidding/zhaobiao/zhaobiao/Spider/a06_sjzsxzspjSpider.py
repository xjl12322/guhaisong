# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time, re
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config
from datetime import datetime
# 网址 http://www.sjzsxzspj.gov.cn


pagenum = config.sjzsxzspj_list[0]  # 翻页深度
threads = config.sjzsxzspj_list[1]  # 线程数
dbname = config.sjzsxzspj_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.sjzsxzspj_list[3])


# 列表链接构造
def list_url():
    zbgg = ['http://www.sjzsxzspj.gov.cn/zfzbgg/index_{}.jhtml'.format(i) for i in range(1, pagenum)]
    zbggs = ['http://www.sjzsxzspj.gov.cn/zfzbgga/index_{}.jhtml'.format(i) for i in range(1, pagenum)]
    bcgg = ['http://www.sjzsxzspj.gov.cn/gzgg/index_{}.jhtml'.format(i) for i in range(1, pagenum)]
    dyly = ['http://www.sjzsxzspj.gov.cn/dyly/index_{}.jhtml'.format(i) for i in range(1, pagenum)]
    return zbgg + zbggs + bcgg + dyly


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//ul[@class="listxxgkul mt10"]/li/a/@href')
                for url in urls:
                    detail_parse(url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="mt20 tc f24 fb lp1"]/text()')
            if len(titles) > 0:
                item['title'] = str(titles[0]).strip()
                item['area_name'] = '石家庄'
                item['source'] = 'http://www.sjzsxzspj.gov.cn'
                date = re.findall('(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)', response)
                item['publish_date'] = str(date[0]) if len(date) > 0 else None
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '石家庄公共资源交易网'
                item['en_name'] = 'Shijiazhuang City Public resource'
                div_html = Html.xpath('//div[@class="neiyeibox fr"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                if 'zfzbgg' in url:
                    item['status'] = '招标公告'
                elif 'zfzbgga' in url:
                    item['status'] = '中标公告'
                elif 'gzgg' in url:
                    item['status'] = '更正公告'
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
