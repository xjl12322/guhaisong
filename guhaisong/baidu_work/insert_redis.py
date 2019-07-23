#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2019/7/20 16:13"
from config_log import config_log
import redis,pymysql,logging
from insert import getDatabase
def inser_redis():
    pool = redis.ConnectionPool(host="127.0.0.1", port=6379, password="", max_connections=1024,decode_responses=True)
    conn_redis = redis.Redis(connection_pool=pool)
    return conn_redis





def get_keyword():
    sql = "select keyword from baidu_ranking"
    cursor = pymysql.cursors.SSCursor(conn)
    cursor.execute(sql)
    while True:
        row = cursor.fetchone()
        if not row:
            logging.info("---------空---------")
            break
        logging.info("获取关键字：{}".format(row[0]))
        num = conn_redis.lpush("keywordlist",row[0])
        if num !=0:
            logging.info("插入redis 第：{}条数据成功".format(num))
        # requests_baidu_keyword(row[0])



if __name__ == "__main__":
    config_log()
    conn = getDatabase()
    conn_redis = inser_redis()
    get_keyword()



