# coding=utf-8
import os
import config
from PublicTools import RedisHelper

path = os.path.dirname(__file__)
RedisHelpers = RedisHelper.Helper()


def helper():
    with open('{}/UserPool.txt'.format(path), 'r', encoding='utf-8')as f:
        lines = f.readlines()

    for line in lines:
        RedisHelpers.push(name=config.usable_user, value=line.strip())
        print(line.strip())


if __name__ == '__main__':
    helper()
