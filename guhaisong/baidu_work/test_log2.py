# -*-coding: utf-8-*-

# **************************file desc*****************************
from test_log import MultiprocessHandler

__author__ = 'yushanshan'
# createTime : 2019/7/30 10:17
# desc : this is new py file, please write your desc for this file
# ****************************************************************


import sys
import time
import multiprocessing

import logging
# 定义日志输出格式
formattler = '%(asctime)s - %(threadName)s - %(levelname)s %(filename)s[:%(lineno)d] - %(message)s'
fmt = logging.Formatter(formattler)
logger = logging.getLogger()
# logger.setLevel(logging.INFO)
logging.basicConfig(logging.INFO, format=fmt)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(fmt)
file_handler = MultiprocessHandler('mylog', when='M')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(fmt)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)


# 发送debug级别日志消息
def test(num):
    time.sleep(10)
    logger.debug('日志测试' + str(num))

if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=3)
    for i in range(10):
        pool.apply_async(func=test, args=(i,))
    pool.close()
    pool.join()
    print('完毕')