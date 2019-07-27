# -*-coding: utf-8-*-

# **************************file desc*****************************
import aiohttp
import functools
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
__author__ = 'yushanshan'
# createTime : 2019/7/18 15:07
# desc : this is new py file, please write your desc for this file
# ****************************************************************
from gevent import monkey;monkey.patch_all()
from insert import getDatabase
from insert_redis import inser_redis
from requests_url import getXpath
import requests,gevent,time
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
# from urllib import parse
import asyncio
from queue import Queue
import gevent.pool
import pymysql, logging, redis
supervisory = ["jd.com", "1688.com", "b2b.baidu.com"]
# from config_log import config_log
from multiprocessing import Pool
from aiohttp import TCPConnector
from config_log import *
Header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36",
}
conn = getDatabase()
import grequests
# q = multiprocessing.Queue(8)
flag_1688 = {}
flag_jd = {}
flag_b2bbaidu = {}

pool_task = gevent.pool.Pool(10)
executor_thread = ThreadPoolExecutor(max_workers=12)
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
    conns = inser_redis()
    # num = conn.llen("keywordlist")
    # for k in range(1, num):
    #     print(k)
    while True:
        result = conns.lpop("keywordlist")
        logging.info("获取关键字：{}".format(result))
        if not result:
            logging.info("list空")
            break
        # requests_baidu_keyword(result)
        logging.info("插入关键字队列：{}".format(result))
        q.put(result)

def requests_keyword():
    pass

def requests_baidu_keyword(keyword="尼龙布"):
    # global q
    # print(111111111111111111111)
    flag = True
    tasks_list = []

    # while flag:
    #     keyword = q.get()
    #     logging.info("获取关键字队列：{}".format(keyword))
        # request_detail(keyword)

def request_detail(keyword):
        list_jd = []
        list_1688 = []
        list_b2bbaidu = []
        tasks_list_result = []
        jd = True
        s_1688 = True
        b2bbaidu = True
        url = "http://www.baidu.com/s?wd=" + keyword
        try:
            r = requests.get(url, headers=Header,timeout=6)
        except Exception as e:
            logging.info("eeeee：{}".format(e))
        else:
            # zloop = asyncio.set_event_loop(zloop)
            zloop = asyncio.get_event_loop()
            tasks = []
            if r:
                tasks_list = []
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
                        index_id = 0
                        index_id = l.xpath("@id")
                        if len(index_id) > 0:
                            index_id = int(index_id[0])
                        # asyncio.ensure_future(fetch(url_baidu_detail,title,keyword,index_id))
                        tasks.append(asyncio.ensure_future(fetch(url_baidu_detail, title, keyword, index_id)))

                zloop.run_until_complete(asyncio.wait(tasks))
            for val in tasks:
                if val.result():
                    print(11111111111111111111111)
                    print(val.result())
                    print(2222222222222222222222222222222)

async def fetch(url,title,keyword,index_id):
    async with aiohttp.ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
        try:
            async with session.get(url, headers = Header,timeout=6) as resp:
                if resp and resp != None:
                    if resp.charset == "utf-8" or resp.charset=="UTF-8" or resp.charset == "utf8":
                        resp.encoding = "utf-8"
                    else:
                        resp.encoding = "gbk"
                    return await resp.text(errors="ignore"),url,title,keyword,index_id
                else:
                    return await None,url,title,keyword,index_id
        except Exception as e:
            logging.info("error2{}".format(e))
            return await None,url,title,keyword,index_id
        # else:
        #     if resp and resp!=None:
        #         if resp.status == 200:
        #             if resp.charset == "utf-8" or resp.charset=="UTF-8" or resp.charset == "utf8":
        #                 resp.encoding = "utf-8"
        #             else:
        #                 resp.encoding = "gbk"

                    # return await resp.text(errors="ignore")

                    # if supervisory[0] in str(resp.url):
                    #     index_id = index_id
                    #     logging.info("关键字{}-- jd 详情页url：{}".format(keyword, resp.url))
                    #     dicts = {}
                    #     dicts["tag"] = "jd"
                    #     dicts["keyword"] = keyword
                    #     if "..." in title:
                    #         html = getXpath(resp.text())
                    #         title = html.xpath('''//head/title/text()''')
                    #         if len(title) > 0:
                    #             title = title[0]
                    #     dicts["title"] = title
                    #     dicts["url"] = resp.url
                    #     dicts["index"] = index_id
                    #     # print(dicts)
                    #     return dicts
                    # if supervisory[1] in str(resp.url):
                    #     flag_1688 = True
                    #     index_id = index_id
                    #     logging.info("关键字{}-- 1688 详情页url：{}".format(keyword, resp.url))
                    #     dicts = {}
                    #     dicts["tag"] = "1688"
                    #     dicts["keyword"] = keyword
                    #     if "..." in title:
                    #         html = getXpath(resp.text())
                    #         title = html.xpath('''//head/title/text()''')
                    #         if len(title) > 0:
                    #             title = title[0]
                    #     dicts["title"] = title
                    #     dicts["url"] = resp.url
                    #     dicts["index"] = index_id
                    #     # print(dicts)
                    #     return dicts
                    # if supervisory[2] in str(resp.url):
                    #     flag_b2bbaidu = True
                    #     index_id = index_id
                    #     logging.info("关键字{}-- b2bbaidu 详情页url：{}".format(keyword, resp.url))
                    #     dicts = {}
                    #     dicts["tag"] = "b2b.baidu.com"
                    #     dicts["keyword"] = keyword
                    #     if "..." in title:
                    #         html = getXpath(resp.text())
                    #         title = html.xpath('''//head/title/text()''')
                    #         if len(title) > 0:
                    #             title = title[0]
                    #     dicts["title"] = title
                    #     dicts["url"] = resp.url
                    #     dicts["index"] = index_id
                    #     # print(dicts)
                    #     return dicts

def sss(obj):
    pass
if __name__ == "__main__":

    config_log()
    s = time.time()
    conn_redis = inser_redis()
    # thread_loop = asyncio.new_event_loop()
    #
    # # 将thread_loop作为参数传递给子线程
    # t = threading.Thread(target=request_detail, args=(thread_loop,))
    # t.daemon = True
    # t.start()
    "2591"
    # while True:
    #     result = conn_redis.lpop("keywordlist")
    #     logging.info("获取关键字：{}".format(result))
    #     if not result:
    #         logging.info("list空")
    #         break
    #     request_detail(keyword = result)

    request_detail("卡佛尼")
    # request_detail("豆角网")

    e = time.time()
    print("xjk")
    j = e-s
    print(j)
    print("3ed")




