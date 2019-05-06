from datetime import datetime
import pymongo

mongo_nodes = 'mongodb://cbi:cbi.123qaz@10.122.44.110:20000,10.122.44.111:20000,10.122.44.112:20000'

host = '10.122.33.93'

class StorageSetting(object):
    def __init__(self,db_name):
        # self.client = pymongo.MongoClient(mongo_nodes)
        self.client = pymongo.MongoClient(host=host,port=27017)
        self.find_db = self.client["gov_zb"]
        self.db_name = db_name
        self.find_collection = self.find_db[self.db_name]

        self.coll_info = self.find_db['zb_all_info']

    def saves(self,result_dic):
        # print(result_dica)
        now = datetime.now()
        try:
            result_dic['create_time'] = now
            self.find_collection.insert(result_dic)
        except Exception as e:
            print("数据重复，存储失败！")
        else:
            print(result_dic['title'])
            item = {}
            item['_id'] = result_dic['_id']
            item['db_name'] = self.db_name
            item['title'] = result_dic['title']
            item['create_time'] = result_dic['create_time']

            try:
                self.coll_info.insert(item)
                print('save successful!')
            except Exception as e:
                print(e)


