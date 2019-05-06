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
# 内蒙古政府采购中心
# nmgzfcg_list = [5, 20, 'nmgzfcg_list_url', 'nmgzfcg_gov_cn']
# http://www.nmgzfcg.gov.cn

pagenum = config.nmgzfcg_list[0]  # 翻页深度
threads = config.nmgzfcg_list[1]  # 线程数
dbname = config.nmgzfcg_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.nmgzfcg_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.nmgzfcg.gov.cn/nmzc/cgxmygg/A0918web_{}.htm'.format(i) for i in
          range(1, pagenum)]
    l2 = ['http://www.nmgzfcg.gov.cn/nmzc/jygg/zbgkyqgg/A094401web_{}.htm'.format(i) for i in
          range(1, pagenum)]
    l3 = ['http://www.nmgzfcg.gov.cn/nmzc/jygg/zbbggg/A094402web_{}.htm'.format(i) for i in
          range(1, pagenum)]
    l4 = ['http://www.nmgzfcg.gov.cn/nmzc/jygg/jzxtpgg/A094403web_{}.htm'.format(i) for i in
          range(1, pagenum)]
    l5 = ['http://www.nmgzfcg.gov.cn/nmzc/jygg/jtbggg/A094404web_{}.htm'.format(i) for i in
          range(1, pagenum)]
    l6 = ['http://www.nmgzfcg.gov.cn/nmzc/jygg/xjcggg/A094405web_{}.htm'.format(i) for i in
          range(1, pagenum)]
    return l1 + l2 + l3 + l4 + l5 + l6
    # return l6

# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//tr/td/li/a/@href')
                for url in urls:
                    detail_parse('http://www.nmgzfcg.gov.cn'+url)
        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        response = request.get(url,type='utf-8')
        if response is not None:
            Html = etree.HTML(response)
            titles = Html.xpath('//div[@class="view"]/dl/dt/text()')
            item['title'] = titles[0] if len(titles)!=0 else None
            if item['title'] is not None:
                item['area_name'] = '内蒙古'
                item['source'] = 'http://www.nmgzfcg.gov.cn'
                date = re.findall('(\d\d\d\d-\d\d-\d\d)', response)
                item['publish_date'] = date[0] if len(date) != 0 else '未公布'

                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['zh_name'] = '内蒙古政府采购中心'
                item['en_name'] = 'NeiMengGu Government Procurement Center'

                div_html = Html.xpath('//div[@class="commain"]')
                content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                             method="html").decode('utf-8')
                item['content_html'] = content_html
                html1 = etree.HTML(content_html)
                if 'xjcggg' in url:
                    item['status'] = '询价采购公告'
                elif 'jtbggg' in url:
                    item['status'] = '竞争性谈判、磋商变更公告'
                elif 'jzxtpgg' in url:
                    item['status'] = '竞争性谈判、磋商公告'
                elif 'zbbggg' in url:
                    item['status'] = '招标（公开、邀请）变更公告'
                elif 'zbgkyqgg' in url:
                    item['status'] = '招标（公开、邀请）公告'
                else:
                    item['status'] = '采购项目预公告'

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
