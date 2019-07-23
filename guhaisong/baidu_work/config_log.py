# -*-coding: utf-8-*-

# **************************file desc*****************************
import platform
import logging
from logging.handlers import TimedRotatingFileHandler

__author__ = 'yushanshan'
# createTime : 2019/7/18 18:23
# desc : this is new py file, please write your desc for this file
# ****************************************************************

def config_log():
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        log_path = './log/'
    else:
        log_path = '/var/log/zanhao/'
    level = logging.INFO
    fmt = '%(asctime)s - %(threadName)s - %(levelname)s %(filename)s[:%(lineno)d] - %(message)s'
    log = logging.getLogger('')

    fileTimeHandler = TimedRotatingFileHandler(log_path + 'DSWebEngine.log', "D", 1, 30)
    fileTimeHandler.suffix = "%Y%m%d.log"
    fileTimeHandler.setFormatter(logging.Formatter(fmt))
    logging.basicConfig(level=level, format=fmt)
    log.addHandler(fileTimeHandler)