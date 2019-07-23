# -*-coding: utf-8-*-

# **************************file desc*****************************
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Process, Pool

__author__ = 'yushanshan'
# createTime : 2019/7/18 15:07
# desc : this is new py file, please write your desc for this file
# ****************************************************************
from insert import getDatabase
from insert_redis import inser_redis
from requests_url import getXpath
import requests, pymysql, logging, redis

from urllib import parse
from queue import Queue

supervisory = ["jd.com", "1688.com", "b2b.baidu.com"]
from config_log import config_log

Header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36",
}
conn = getDatabase()
q = Queue(15)


def test_connection():
    try:
        global conn
        conn.ping()
    except:
        conn = getDatabase()
    return conn


def insert_db(dicts):
    supervisory = {"jd.com": ["jd", "jd_title", "jd_url"], "1688.com": ["1688", "1688_title", "1688_url"],
                   "b2b.baidu.com": ["b2bbaidu", "b2bbaidu_title", "b2bbaidu_url"]}
    if dicts.get("tag") == "jd":
        print(dicts)
        sql = "update baidu_ranking set jd=%d,jd_title='%s',jd_url='%s' where keyword='%s'" % (
        dicts["index"], dicts["title"], dicts["url"], dicts["keyword"])
        conn = test_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
            logging.info("jd--mysql:{}".format("插入成功"))
        except Exception as e:
            conn.rollback()
            logging.info("jd--mysql:{}".format(e))

    if dicts.get("tag") == "1688":
        print(dicts)
        sql = "update baidu_ranking set `1688`=%d,1688_title='%s',1688_url='%s' where keyword='%s'" % (
        dicts["index"], dicts["title"], dicts["url"], dicts["keyword"])
        conn = test_connection()
        cur = conn.cursor()
        conn.ping(reconnect=True)
        try:
            cur.execute(sql)
            conn.commit()
            logging.info("1688--mysql:{}".format("插入成功"))
        except Exception as e:
            conn.rollback()
            logging.info("1688--mysql:{}".format(e))

    if dicts.get("tag") == "b2b.baidu.com":
        print(dicts)
        sql = "update baidu_ranking set b2bbaidu=%d,b2bbaidu_title='%s',b2bbaidu_url='%s' where keyword='%s'" % (
        dicts["index"], dicts["title"], dicts["url"], dicts["keyword"])
        conn = test_connection()
        cur = conn.cursor()
        # conn.ping(reconnect=True)
        try:
            cur.execute(sql)
            conn.commit()
            logging.info("b2b.baidu.com--mysql:{}".format("插入成功"))
        except Exception as e:
            conn.rollback()
            logging.info("b2b.baidu.com--mysql:{}".format(e))


def get_keyword(q):
    conn = inser_redis()
    num = conn.llen("keywordlist")
    for k in range(557, num):
        print(k),
        result = conn.lindex("keywordlist", k)
        q.put(result)
        # requests_baidu_keyword(result)


def requests_keyword():
    pass


def requests_baidu_keyword(q):
    while True:
        keyword = q.get()
        flag_jd = False
        flag_1688 = False
        flag_b2bbaidu = False
        url = "http://www.baidu.com/s?wd=" + keyword
        r = requests.get(url, headers=Header)
        if r:
            logging.info("请求关键字成功：{}".format(url))
            selector = getXpath(r.text)
            node_list = selector.xpath('''//div[contains(@class,"c-container")]''')
            for l in node_list:
                url_baidu_detail = l.xpath('''h3/a[1]/@href''')
                lingshi_title = l.xpath('''string(h3/a[1])''')
                title = str(lingshi_title)
                if len(url_baidu_detail) > 0:
                    url_baidu_detail = url_baidu_detail[0]
                    if url_baidu_detail == "" or len(url_baidu_detail) < 3:
                        continue
                    if str(url_baidu_detail).startswith("/sf/"):
                        continue
                    try:
                        r2 = requests.get(url_baidu_detail, headers=Header, verify=False, timeout=8)
                    except Exception as e:
                        logging.warning(e)
                    else:
                        if r2:
                            if r2.apparent_encoding == "utf-8" or r2.apparent_encoding.startswith(
                                    "UTF-8") or r2.apparent_encoding == "utf8":
                                r2.encoding = "utf-8"
                            elif r2.apparent_encoding == "GB2312" or r2.apparent_encoding.startswith(
                                    "ISO-8859") or r2.apparent_encoding.startswith("Windows"):
                                r2.encoding = "gbk"
                            if r2:
                                print(r2.url)
                                if supervisory[0] in r2.url and flag_jd == False:
                                    flag_jd = True
                                    index_id = 0
                                    index_id = l.xpath("@id")
                                    if len(index_id) > 0:
                                        index_id = int(index_id[0])
                                    logging.info("关键字{}-- jd 详情页url：{}".format(keyword, r2.url))
                                    dicts = {}
                                    dicts["tag"] = "jd"
                                    dicts["keyword"] = keyword
                                    if "..." in title:
                                        html = getXpath(r2.text)
                                        title = html.xpath('''//head/title/text()''')
                                        if len(title) > 0:
                                            title = title[0]
                                    dicts["title"] = title
                                    dicts["url"] = r2.url
                                    dicts["index"] = index_id
                                    insert_db(dicts)
                                if supervisory[1] in r2.url and flag_1688 == False:
                                    flag_1688 = True
                                    index_id = 0
                                    index_id = l.xpath("@id")
                                    if len(index_id) > 0:
                                        index_id = int(index_id[0])
                                    logging.info("关键字{}-- 1688 详情页url：{}".format(keyword, r2.url))
                                    dicts = {}
                                    dicts["tag"] = "1688"
                                    dicts["keyword"] = keyword
                                    if "..." in title:
                                        html = getXpath(r2.text)
                                        title = html.xpath('''//head/title/text()''')
                                        if len(title) > 0:
                                            title = title[0]
                                    dicts["title"] = title
                                    dicts["url"] = r2.url
                                    dicts["index"] = index_id
                                    insert_db(dicts)
                                if supervisory[2] in r2.url and flag_b2bbaidu == False:
                                    flag_b2bbaidu = True
                                    index_id = 0
                                    index_id = l.xpath("@id")
                                    if len(index_id) > 0:
                                        index_id = int(index_id[0])
                                    logging.info("关键字{}-- b2bbaidu 详情页url：{}".format(keyword, r2.url))
                                    dicts = {}
                                    dicts["tag"] = "b2b.baidu.com"
                                    dicts["keyword"] = keyword
                                    if "..." in title:
                                        html = getXpath(r2.text)
                                        title = html.xpath('''//head/title/text()''')
                                        if len(title) > 0:
                                            title = title[0]

                                    dicts["title"] = title
                                    dicts["url"] = r2.url
                                    dicts["index"] = index_id
                                    insert_db(dicts)


if __name__ == "__main__":
    config_log()

    t1 = threading.Thread(target=get_keyword, args=(q,))
    t1.start()
    t2 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t2.start()
    t3 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t3.start()
    t4 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t4.start()
    t5 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t5.start()
    t6 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t6.start()
    t7 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t7.start()
    t8 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t8.start()
    t9 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t9.start()
    t10 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t10.start()
    t11 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t11.start()
    t12 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t12.start()
    t13 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t13.start()
    t14 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t14.start()
    t15 = threading.Thread(target=requests_baidu_keyword, args=(q,))
    t15.start()


    # pool = Pool()
    # for k in range(1, 5):
    #     result = pool.apply_async(requests_baidu_keyword,(q,))
    #     # rl = pool.map(get_keyword, testFL)
    # pool.close()
    # pool.join()






    # get_keyword()
    # requests_baidu_keyword("儿童高跟鞋")
