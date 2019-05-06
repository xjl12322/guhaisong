# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time, re
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config
from datetime import datetime
# 网址 http://www.gzggzy.cn


pagenum = config.gzggzy_list[0]  # 翻页深度
threads = config.gzggzy_list[1]  # 线程数
dbname = config.gzggzy_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.gzggzy_list[3])


# 列表链接构造
def list_url():
    api = 'http://www.gzggzy.cn/cms/wz/view/index/layout2/zfcglist.jsp?siteId=1&channelId='
    cggg = [api + '456&siteId=1&page={}'.format(i) for i in range(1, pagenum)]
    ygg = [api + '448&siteId=1&page={}'.format(i) for i in range(1, pagenum)]
    gzgg = [api + '457&siteId=1&page={}'.format(i) for i in range(1, pagenum)]
    jggg = [api + '458&siteId=1&page={}'.format(i) for i in range(1, pagenum)]
    return cggg + ygg + gzgg + jggg


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//td/a/@href')
                for url in urls:
                    times = html.xpath('//a[@href="{}"]/../following-sibling::td/text()'.format(url))
                    titles = html.xpath('//a[@href="{}"]/text()'.format(url))
                    if len(titles) != 0:
                        url = 'http://www.gzggzy.cn' + url + '***' + times[0] + '***' + titles[0] if len(
                            times) != 0 else '0000-00-00'
                        detail_parse(url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        publish = url.split('***')[1]
        title = url.split('***')[2]
        url = url.split('***')[0]
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            # titles = Html.xpath('//p[@align="center"]//text()')
            # if len(titles) > 0:
            item['title'] = title
            item['area_name'] = '广州'
            item['source'] = 'http://www.gzggzy.cn'
            # date = re.findall('(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)', response)
            item['publish_date'] = publish
            item['detail_url'] = url
            item['create_time'] = datetime.now()
            item['zh_name'] = '广州公共资源交易中心'
            item['en_name'] = 'Guangzhou City Government Procurement'
            div_html = Html.xpath('//div[@class="xx-text"]')
            content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                         method="html").decode('utf-8')
            item['content_html'] = content_html
            html1 = etree.HTML(content_html)
            if 'channelId=456' in url:
                item['status'] = '采购公告'
            elif 'channelId=448' in url:
                item['status'] = '预公告'
            elif 'channelId=457' in url:
                item['status'] = '更正公告'
            else:
                item['status'] = '结果公告'
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
