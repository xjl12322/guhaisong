# coding=utf-8
import config
from pymongo import MongoClient


class Helper:
    def __init__(self):
        self.client = MongoClient(config.mongo_nodes)[config.mongo_db]

    def push(self, collection, item, key):
        collect = self.client[collection]
        try:
            item['_id'] = key
            collect.insert(item)
            print('Save Success:', key)
        except Exception as e:
            print('Save Failed:', item, e)
            
    def update(self, collection, item, key):
        collect = self.client[collection]
        try:
            item['_id'] = key
            collect.update({'_id':key},{'$set':item})
            print('update Success:', key)
        except Exception as e:
            print('update Failed:', key, e)
    

    def select(self,collection, condition):
        collect = self.client[collection]
        items = collect.find(condition)
        # from pprint import pprint
        # pprint([item for item in items])
        return [item for item in items]
    
    def select_limit(self,collection,condition,limits):
        collect = self.client[collection]
        items = collect.find(condition).limit(limits)
        # from pprint import pprint
        # pprint([item for item in items])
        return [item for item in items]



if __name__ == '__main__':
    start = Helper()
    a = start.select('tyc_investment_log',{'investor_id':'22822'})
    print(a)
