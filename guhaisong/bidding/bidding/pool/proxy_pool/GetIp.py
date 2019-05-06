# coding:utf-8

from Api import mogu_proxy
import gevent
import requests
import pymysql
import time
import config



class CheckIp(object):
    def __init__(self):
        # 打开数据库连接
        self.db = pymysql.connect(host=config.host, user=config.user, password=config.password, db=config.db, port=config.port)
        self.url = 'https://www.baidu.com/'

    def check_proxy(self, ip):
        # 验证代理有效性
        proxies = {'http': 'http://'+ip}
        try:
            res = requests.get(url=self.url, proxies=proxies, timeout=2)
        except:
            pass
        else:
            self.save_mysql(ip)

    def save_mysql(self, ip):
        # 使用cursor()方法获取操作游标 
        cursor = self.db.cursor()
        time_temp = int((time.time())*1000)
        # print(time_temp)
        print(ip)
        
        # SQL 插入语句
        sql = """INSERT INTO proxy_pool(ip,
                status, time_temp)
                VALUES (%s, %s, %s)"""
        try:
            # 执行sql语句
            cursor.execute(sql, (ip,0,time_temp))
            # 提交到数据库执行
            self.db.commit()
        except:
            # 如果发生错误则回滚
            self.db.rollback()
        finally:
            # 关闭数据库连接
            self.db.close()

    # CREATE TABLE table1(Id int primary key auto_increment, ip varchar(30),status varchar(10), time_temp varchar(20));

    def run(self):
        # 调用接口获取代理ip
        item = mogu_proxy.get()
        if len(item) < 1:
            return
        spawns = [gevent.spawn(self.check_proxy,ip) for ip in item]
        gevent.joinall(spawns)
    
    def main(self):
        while True:
            self.run()
            time.sleep(5)


if __name__ == '__main__':
    cip = CheckIp()
    cip.main()
