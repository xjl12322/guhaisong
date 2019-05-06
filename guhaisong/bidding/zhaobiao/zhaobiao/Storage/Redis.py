# coding=utf-8
from rediscluster import StrictRedisCluster
import config


class save():
    def __init__(self):
        try:
            self.client = StrictRedisCluster(
                startup_nodes=config.redis_nodes,
                password=config.redis_pass,
            )
        except Exception as e:
            print(e)

    def push(self, name, value, type=None):
        try:
            self.client.lpush(name, value) if type is None else self.client.rpush(name, value)
            print('redis save success:{}'.format(value))
        except Exception as e:
            print(e)

    def pop(self, name, type=None):
        try:
            bvalue = self.client.lpop(name) if type is None else self.client.rpop(name)
            return None if bvalue is None else str(bvalue, encoding='utf-8')
        except Exception as e:
            print(e)

    def judge(self, name):
        return self.client.exists(name)


if __name__ == '__main__':
    start = save()
    # for i in range(30):
    #     start.push('tt', 'test')
    # print(start.pop('tt'))