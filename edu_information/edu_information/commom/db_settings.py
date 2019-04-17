#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2019/1/28 22:36"

from main import cus
CONRENT_CONF = cus

SQLDB = {
    "local":{"MYSQL_HOST": "127.0.0.1",
"MYSQL_DBNAME" : "test",
"MYSQL_PORT" : 3306,
"MYSQL_USER" : "root",
"MYSQL_PASSWD" : "mysql"},

    "line":{"MYSQL_HOST": "47.97.18.252",
"MYSQL_DBNAME" : "ecms72g",
"MYSQL_PORT" : 3306,
"MYSQL_USER" : "ecms",
"MYSQL_PASSWD" : "ecms2mA5ycQmau8KiAXf0yh"},

}
REDISDB = {
    "local":{"REDIS_HOST": "127.0.0.1",
            "REDIS_PORT" : 6379,
            "REDIS_DB":10,
            "REDIS_PASSWORD" : None},

    "line":{"REDIS_HOST": "47.97.18.252",
"REDIS_PORT" : 6379,
"REDIS_DB":11,
"REDIS_PASSWORD" : "redisBTQR94srKxslBBOph2V"},

}

#scrapy-redis 指定数据库

# REDIS_URL = 'redis://:xinnet@127.0.0.1:6379'
# REDIS_URL = 'redis://:xinnet123@127.0.0.1:6379'
# REDIS_URL = 'redis://@127.0.0.1:6379'
# REDIS_HOST = '127.0.0.1'
# REDIS_PORT = 6379
