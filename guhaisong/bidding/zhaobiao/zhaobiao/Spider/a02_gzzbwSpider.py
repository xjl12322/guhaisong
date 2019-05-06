# coding=utf-8
import gevent
from gevent import monkey;monkey.patch_all()
import config
import json
import re, time
from Parse import request
from Storage import Redis, Mongo
from lxml import etree
# 网址 http://www.gzzbw.cn
from datetime import datetime

pagenum = config.gzzbw_list[0]  # 翻页深度
threads = config.gzzbw_list[1]  # 线程数
dbname = config.gzzbw_list[2]  # 列表url队列

# 数据存储实例化
save = Redis.save()
Save = Mongo.save(config.gzzbw_list[3])


# 列表链接构造
def list_url():
    api = 'http://www.gzzbw.cn/api/trade/search?pubDate=all&region=5200&industry=all&prjType=all&noticeType=all&noticeClassify=all&pageIndex={}&args='
    zhaobs = [api.format(i) for i in range(1, pagenum)]
    return zhaobs


# 列表解析(详情url)
def list_parse():
    while True:
        list_url = save.pop(name=dbname)
        if list_url is not None:
            response = request.get(list_url, header={'Accept': '*/*', })
            if response is not None:
                ids = re.findall('"Id":(\d{1,10}),', response)
                for id in ids:
                    detail_parse(id)
        else:
            break


# 详情解析
def detail_parse(id):
    if id is not None:
        url = 'http://www.gzzbw.cn/api/trade/{}'.format(id)
        item = {}
        response = request.get(url, header={'Accept': '*/*', })
        if response is not None:
            res = json.loads(response)
            title = res['Title'] if 'Title' in response else None
            if title is not None:
                item['title'] = str(title).replace('\r', '').replace('\n', '')
                item['area_name'] = '贵州'
                item['source'] = 'http://www.gzzbw.cn'
                item['publish_date'] = res['PublishDate']
                item['detail_url'] = url
                item['create_time'] = datetime.now()
                item['content_html'] = res['Content']
                item['zh_name'] = '贵州省招标投标公共服务平台'
                item['en_name'] = 'Guizhou Tender Public Service Platform'
                html_1 = etree.HTML(res['Content'])
                timezones = res['Timezones']
                status = ''
                for timezone in timezones:
                    if "'Id': {}".format(id) in str(timezone):
                        status = timezone['BTypeName']
                item['status'] = status
                Save.push(item=item, key=id)


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
    # list_parse()
