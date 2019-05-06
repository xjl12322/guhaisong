# coding=utf-8
from gevent import monkey;monkey.patch_all()
import gevent
import time, re
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config

from datetime import datetime
# 网址 http://ggzy.sz.gov.cn


pagenum = config.szggzy_list[0]  # 翻页深度
threads = config.szggzy_list[1]  # 线程数
dbname = config.szggzy_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.szggzy_list[3])


# 列表链接构造
def list_url():
    gg = ['http://ggzy.sz.gov.cn/jyxx/zfcgxm/zbgg_zf/', 'http://ggzy.sz.gov.cn/jyxx/zfcgxm/zbcjgg_zf/']
    zbgg = ['http://ggzy.sz.gov.cn/jyxx/zfcgxm/zbcjgg_zf/index_{}.htm'.format(i) for i in range(1, pagenum)]
    zbcjgg = ['http://ggzy.sz.gov.cn/jyxx/zfcgxm/zbgg_zf/index_{}.htm'.format(i) for i in range(1, pagenum)]
    return gg + zbgg + zbcjgg


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//ul[@class="list"]/li/a/@href')
                for url in urls:
                    if 'zbcjgg_zf' in list_url:
                        url = 'http://ggzy.sz.gov.cn/jyxx/zfcgxm/zbcjgg_zf' + str(url).replace('./', '/')
                    else:
                        url = 'http://ggzy.sz.gov.cn/jyxx/zfcgxm/zbgg_zf' + str(url).replace('./', '/')
                    detail_parse(url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url,type='utf-8')
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="sub-xx-tit"]/text()')
            if len(titles) > 0:
                item['title'] = str(titles[0]).strip()
                item['area_name'] = '深圳'
                item['source'] = 'http://ggzy.sz.gov.cn'
                # date = re.findall('(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)', response)
                item['publish_date'] = (''.join(Html.xpath('//div[@class="sub-xx-time"]/text()'))).strip('发表时间：')
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '深圳市公共资源交易平台'
                item['en_name'] = 'Shenzhen Public resource'
                div_html = Html.xpath('//div[@class="sub-warp"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                states = Html.xpath('//div[@class="weizhi"]/a/text()')
                item['status'] = states[-1] if len(states) != 0 else None
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
