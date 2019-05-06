# coding=utf-8
import hashlib
from pymongo import MongoClient
from Config import config

conn = MongoClient(
    host=config.host,
    port=config.port,
)
db = conn[config.db]
client_a = db[config.collect_a]
client_b = db[config.collect_b]
client_c = db[config.collect_c]


def _Md5(string):
    hl = hashlib.md5()
    hl.update(string.encode(encoding='utf-8'))
    hash = hl.hexdigest()
    return hash[8:-8]


# 保存字符映射
def save_font(items):
    try:
        client_a.insert(items)
    except:
        pass


# 去重检测
def repeated_detect(code):
    try:
        client_b.insert({"_id": code})
        return 'yes'
    except:
        return 'no'


# 查询
def search(code):
    items = client_a.find({'_id': code})
    try:
        item = items[0]
        return item['mapping']
    except:
        return {}


# 保存内容
def save_con(content):
    try:
        client_c.insert({"data": content})
    except:
        pass


if __name__ == '__main__':
    search()
