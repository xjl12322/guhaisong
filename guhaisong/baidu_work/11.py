# -*-coding: utf-8-*-

# **************************file desc*****************************
__author__ = 'yushanshan'
# createTime : 2019/7/18 15:07
# desc : this is new py file, please write your desc for this file
# ****************************************************************
from insert import getDatabase
from requests_url import getXpath
import requests, pymysql, logging
from urllib import parse

supervisory = ["jd.com", "1688.com", "b2b.baidu.com"]

from config_log import config_log

Header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36",
}
conn = getDatabase()


def insert_db(dicts):
    supervisory = {"jd.com":["jd","jd_title","jd_url"], "1688.com":["1688","1688_title","1688_url"], "b2b.baidu.com":["b2bbaidu","b2bbaidu_title","b2bbaidu_url"]}
    if dicts.get("tag") == "jd":
        sql = "update baidu_ranking set jd=%d,jd_title='%s',jd_url='%s' where keyword='%s'"%(dicts["index"],dicts["title"],dicts["url"],dicts["keyword"])
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
            logging.info("jd--mysql:{}".format("插入成功"))
        except Exception as e:
            conn.rollback()
            logging.info("jd--mysql:{}".format(e))

    if dicts.get("tag") == "1688":
        sql = "update baidu_ranking set 1688=%d,1688_title='%s',1688_url='%s' where keyword='%s'"%(dicts["index"],dicts["title"],dicts["url"],dicts["keyword"])
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
            logging.info("1688--mysql:{}".format("插入成功"))
        except Exception as e:
            conn.rollback()
            logging.info("1688--mysql:{}".format(e))


    if dicts.get("tag") == "b2b.baidu.com":
        print(dicts)
        sql = "update baidu_ranking set b2bbaidu=%d,b2bbaidu_title='%s',b2bbaidu_url='%s' where keyword='%s'"%(dicts["index"],dicts["title"],dicts["url"],dicts["keyword"])
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
            logging.info("b2b.baidu.com--mysql:{}".format("插入成功"))
        except Exception as e:
            conn.rollback()
            logging.info("b2b.baidu.com--mysql:{}".format(e))

def get_keyword():
    sql = "select keyword from baidu_ranking"
    cursor = pymysql.cursors.SSCursor(conn)
    cursor.execute(sql)
    while True:
        row = cursor.fetchone()
        if not row:
            break
        requests_baidu_keyword(row[0])


def requests_baidu_keyword(keyword):
    url = "http://www.baidu.com/s?wd=" + keyword
    r = requests.get(url, headers=Header)
    if r:
        # print(r.url)'''//head/title/text()'''
        logging.info("请求关键字成功：{}".format(url))
        selector = getXpath(r.text)
        node_list = selector.xpath('''//div[contains(@class,"c-container")]''')
        for index,l in enumerate(node_list,1):
            url_baidu_detail = l.xpath('''h3/a[1]/@href''')
            lingshi_title = l.xpath('''string(h3/a[1])''')
            title = str(lingshi_title)
            if len(url_baidu_detail)>0:
                url_baidu_detail = url_baidu_detail[0]
                if url_baidu_detail == "" or len(url_baidu_detail)<3:
                    continue
                r2 = requests.get(url_baidu_detail, headers=Header)
                if r2:
                    if supervisory[0] in r2.url:
                        logging.info("关键字{}-- jd 详情页url：{}".format(keyword,r2.url))
                        dicts = {}
                        dicts["tag"] = "jd"
                        dicts["keyword"] = keyword
                        if "..." in lingshi_title:
                            html = getXpath(r2.text)
                            title = html.xpath('''//head/title/text()''')
                        dicts["title"] = title
                        dicts["url"] = r2.url
                        dicts["index"] =index
                        insert_db(dicts)

                    if supervisory[1] in r2.url:
                        logging.info("关键字{}-- 1688 详情页url：{}".format(keyword, r2.url))
                        dicts = {}
                        dicts["tag"] = "1688"
                        dicts["keyword"] = keyword
                        if "..." in lingshi_title:
                            html = getXpath(r2.text)
                            title = html.xpath('''//head/title/text()''')
                        dicts["title"] = title
                        dicts["url"] = r2.url
                        dicts["index"] =index
                        insert_db(dicts)


                    if supervisory[2] in r2.url:
                        logging.info("关键字{}-- b2bbaidu 详情页url：{}".format(keyword, r2.url))
                        dicts = {}
                        dicts["tag"] = "b2b.baidu.com"
                        dicts["keyword"] = keyword
                        if "..." in lingshi_title:
                            html = getXpath(r2.text)
                            title = html.xpath('''//head/title/text()''')
                        dicts["title"] = title
                        dicts["url"] = r2.url
                        dicts["index"] =index
                        insert_db(dicts)



if __name__ == "__main__":
    config_log()

    get_keyword()
