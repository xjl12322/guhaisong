import redis
from rediscluster import StrictRedisCluster
from utils import config


class save():
    def __init__(self):
        try:
            self.client = StrictRedisCluster(startup_nodes=config.redis_nodes,password=config.redis_pass,)
        except Exception as e:
            print(e)

class Rdis_Queue(object):
    def __init__(self,host, dblist, dbset):
        self.pool = redis.ConnectionPool(host=host, port=6379, decode_responses=True)
        self.r = redis.Redis(connection_pool=self.pool)

        self.dblist =dblist
        self.dbset = dbset

    def pull_to_rlist(self, urls):
        '''往列表添加ulr'''
        try:
            self.r.rpush(self.dblist, urls)
        except Exception as e:
            print('添加rlist失败：'.format(e))

    def r_len(self):
        try:
            lens = self.r.llen(self.dblist)
        except Exception as e:
            print('r_len出错：'.format(e))
            return None
        else:
            return lens


    def get_to_rlist(self):
        '''从列表取url，并删除'''
        try:
            url = self.r.lpop(self.dblist)
        except Exception as e:
            print('get_rlist失败：'.format(e))
            return None
        else:
            return  url

    def rset_info(self):
        try:
            r_info = list(self.r.smembers(self.dbset))
        except Exception as e:
            print('rset_info出错：'.format(e))
            return None
        else:
            return r_info


    def add_to_rset(self, urls):
        '''添加url进rset'''
        try:
            self.r.sadd(self.dbset, urls)
        except Exception as e:
            print('add_rset失败：'.format(e))


    def in_rset(self, urls):
        return self.r.sismember(self.dbset, urls)



if __name__ == '__main__':
    start = Rdis_Queue(host='localhost', dblist='neimeng_list1', dbset='neimeng_set1')
    a = start.get_to_rlist()
    print(a)
    b = eval(a)
    print(b)














