# -*-coding: utf-8-*-

# **************************file desc*****************************
import platform
import logging
from logging.handlers import TimedRotatingFileHandler
import logging
from logging import handlers
__author__ = 'yushanshan'
# createTime : 2019/7/18 18:23
# desc : this is new py file, please write your desc for this file
# ****************************************************************

# def config_log():
#     if platform.system() == 'Windows' or platform.system() == 'Darwin':
#         log_path = './log/'
#     else:
#         log_path = '/var/log/zanhao/'
#     level = logging.INFO
#     fmt = '%(asctime)s - %(threadName)s - %(levelname)s %(filename)s[:%(lineno)d] - %(message)s'
#     log = logging.getLogger('')
#
#     fileTimeHandler = TimedRotatingFileHandler(log_path + 'DSWebEngine.log', "D", 1, 3)
#     fileTimeHandler.suffix = "%Y%m%d.log"
#     fileTimeHandler.setFormatter(logging.Formatter(fmt))
#     logging.basicConfig(level=level, format=fmt)
#     log.addHandler(fileTimeHandler)
import sys
from test_log import MultiprocessHandler
def config_log():
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        log_path = './log/'
    else:
        log_path = '/var/log/zanhao/'
    level = logging.INFO
    formattler = '%(asctime)s - %(threadName)s - %(levelname)s %(filename)s[:%(lineno)d] - %(message)s'
    fmt = logging.Formatter(formattler)
    logger = logging.getLogger()
    # logger.setLevel(logging.INFO)
    logging.basicConfig(level=level, format=fmt)
    # stream_handler = logging.StreamHandler(sys.stdout)
    # stream_handler.setLevel(logging.INFO)
    # stream_handler.setFormatter(fmt)
    file_handler = MultiprocessHandler('mylog', when='M')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)
    # logger.addHandler(stream_handler)
    logger.addHandler(file_handler)