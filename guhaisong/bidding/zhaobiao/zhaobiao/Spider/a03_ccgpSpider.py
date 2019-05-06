# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import time
from Parse import request
from lxml import etree, html
from Storage import Redis, Mongo
import config
from datetime import datetime
# 网址 http://zzcg.ccgp.gov.cn


pagenum = config.ccgp_list[0]  # 翻页深度
threads = config.ccgp_list[1]  # 线程数
dbname = config.ccgp_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.ccgp_list[3])


# 列表链接构造
def list_url():
    zbgg = ['http://zzcg.ccgp.gov.cn/zbgg/index_{}.jhtml'.format(i) for i in range(1,pagenum)]
    bggg = ['http://zzcg.ccgp.gov.cn/bggg/index_{}.jhtml'.format(i) for i in range(1,pagenum)]
    jggg = ['http://zzcg.ccgp.gov.cn/jggg/index_{}.jhtml'.format(i) for i in range(1,pagenum)]
    qtgg = ['http://zzcg.ccgp.gov.cn/qtgg/index_{}.jhtml'.format(i) for i in range(1,pagenum)]
    xecgxm = ['http://zzcg.ccgp.gov.cn/xecgxm/index_{}.jhtml'.format(i) for i in range(1,pagenum)]
    return zbgg + bggg + jggg + qtgg + xecgxm


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//div[@class="List2 Top8"]//li/a/@href')
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
            titles = Html.xpath('//h1[@class="TxtCenter Padding10 BorderEEEBottom"]/text()')
            if len(titles) > 0:
                item['title'] = titles[0]
                item['area_name'] = '全国'
                item['source'] = 'http://zzcg.ccgp.gov.cn'
                date = Html.xpath('//div[@class="TxtCenter Padding10"]/text()')
                item['publish_date'] = str(date[0]).replace('发布时间：', '') if len(date) > 0 else None
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '中共中央直属机关采购中心'
                item['en_name'] = 'Purchase Center of CPC Centra Committee Departments'
                div_html = Html.xpath('//div[@class="Padding10 BorderCCCDot F14"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                if 'zbgg' in url:
                    item['status'] = '招标公告'
                elif 'bggg' in url:
                    item['status'] = '变更公告'
                elif 'jggg' in url:
                    item['status'] = '结果公告'
                elif 'qtgg' in url:
                    item['status'] = '其他公告'
                else:
                    item['status'] = '目录外限额下采购项目'
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
