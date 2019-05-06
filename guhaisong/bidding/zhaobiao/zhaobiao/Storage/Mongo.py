# coding=utf-8
from pymongo import MongoClient
import hashlib
import config



class save():
    def __init__(self, mongo_collection):
        # self.conn = MongoClient(host=config.mongo_host, port=config.mongo_port)
        #self.conn = MongoClient(config.mongo_nodes)
        #self.db = self.conn[config.mongo_db]
        
        # self.db.authenticate(name=config.mongo_user, password=config.mongo_pass)  # 认证
        self.conn = MongoClient(host='10.122.33.93',port=27017)
        self.db = self.conn['gov_zb']
        
        self.collection = self.db[mongo_collection]

    def md5(self, string):
        string = str(string)
        hl = hashlib.md5()
        hl.update(string.encode(encoding='utf-8'))
        return hl.hexdigest()[8:-8]

    def push(self, item, key):
        item['_id'] = self.md5(key)
        try:
            self.collection.insert(item)
            print('save success:{}'.format([item['title']]))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    start = save('aaa')
    start.push({'test': 1}, 3)
