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
# 太原市政府采购
# tyzfcg_list = [5, 20, 'tyzfcg_list_url', 'tyzfcg_gov_cn']
# http://www.tyzfcg.gov.cn

pagenum = config.tyzfcg_list[0]  # 翻页深度
threads = config.tyzfcg_list[1]  # 线程数
dbname = config.tyzfcg_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.tyzfcg_list[3])


# 列表链接构造
def list_url():
    l1 = ['http://www.tyzfcg.gov.cn/view.php?app=bid&type=A&id_name=&page={}'.format(i) for i in
          range(1, pagenum)]
    l2 = ['http://www.tyzfcg.gov.cn/view.php?app=bid&type=B&id_name=&page={}'.format(i) for i in
          range(1, pagenum)]
    l3 = ['http://www.tyzfcg.gov.cn/view.php?app=bid&type=D&id_name=&page={}'.format(i) for i in
          range(1, pagenum)]
    return l1 + l2 + l3
    # return test


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url)
            if response is not None:
                html = etree.HTML(response)
                urls = html.xpath('//tr[contains(@class,"pt2")]/@onclick')
                for url in urls:
                    titles = html.xpath('//tr[@onclick="{}"]//a/text()'.format(url))
                    if len(titles) != 0:
                        title = titles[0]
                        detail_parse(
                            'http://www.tyzfcg.gov.cn/view.php?app=bidDetail&id=' + str(url).strip('fDetail(').strip(
                                ')') + '**' + title)

        else:
            break


# 详情解析
def detail_parse(url):
    if url is not None:
        item = {}
        title = url.split('**')[-1]
        url = url.split('**')[0]
        response = request.get(url)
        if response is not None:
            Html = etree.HTML(response)
            item['title'] = title
            item['area_name'] = '太原'
            item['source'] = 'http://www.tyzfcg.gov.cn/'
            date = re.findall('发布时间:(\d\d\d\d-\d\d-\d\d)', response)

            item['publish_date'] = date[0] if len(date) != 0 else '未公布'

            item['detail_url'] = url
            item['create_time'] = datetime.now()
            item['zh_name'] = '太原市政府采购中心'
            item['en_name'] = 'Taiyuan Government Procurement Center'

            div_html = Html.xpath('//tr[@class="bk5"]')
            content_html = html.tostring(div_html[0], encoding='utf-8', pretty_print=True,
                                         method="html").decode('utf-8')
            item['content_html'] = content_html
            html1 = etree.HTML(content_html)
            states = re.findall('--(.*?)--正文', response)
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
