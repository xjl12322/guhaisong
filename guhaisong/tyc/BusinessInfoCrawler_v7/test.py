import pymongo
import pymongo
import hashlib
import jieba
import re

uri = 'mongodb://cbi:cbi.123qaz@10.122.44.110:20000,10.122.44.111:20000,10.122.44.112:20000'
uri2 = 'mongodb://10.122.33.93:27017'
uri3 = 'mongodb://127.0.0.1:27017'

find_cli = pymongo.MongoClient (uri3)
save_cli = pymongo.MongoClient (uri2)

def save_mon(db, table, data):
    try:
        table = 'dcg_20190129_tycdeal_remain_tyc'
        save_cli[db][table].insert (data)
    except Exception as e:
        print ('--------------------存储失败！', e)
    else:
        pass


def find_db():
    db = 'codes'
    table_name = 'dcg_20190129_tycdeal_remain3_tyc'
    find_coll = find_cli[db][table_name]
    try:
        for data in find_coll.find ():
            save_mon (db, table_name, data)
    except:
        pass

if __name__ == '__main__':
    find_db ()

