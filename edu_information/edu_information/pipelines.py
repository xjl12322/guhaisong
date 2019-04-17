# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
from twisted.enterprise import adbapi
import pymysql
import logging
from scrapy import log

from .commom.db_settings import SQLDB,REDISDB,CONRENT_CONF

class EduInformationPipeline(object):

    def process_item(self, item, spider):
        return item


# logger = logging.getLogger(__name__)
class mysql_yi_pipelines(object):

    '''异步写入'''
    def __init__(self):




        dbargs = dict(
        host = SQLDB[CONRENT_CONF]["MYSQL_HOST"],
        port=SQLDB[CONRENT_CONF]["MYSQL_PORT"],
        db = SQLDB[CONRENT_CONF]["MYSQL_DBNAME"],
        user = SQLDB[CONRENT_CONF]["MYSQL_USER"],  # replace with you user name
        passwd = SQLDB[CONRENT_CONF]["MYSQL_PASSWD"],  # replace with you password
        charset = 'utf8',
        cursorclass = pymysql.cursors.DictCursor,
        use_unicode = False,
)
        self.dbpool = adbapi.ConnectionPool('pymysql', **dbargs)


    # @classmethod
    # def from_settings(cls,settings):
    #     # 先将setting中连接数据库所需内容取出，构造一个地点
    #     dbparams = dict(
    #         host=settings['MYSQL_HOST'],  # 读取settings中的配置
    #         db=settings['MYSQL_DBNAME'],
    #         port=settings['MYSQL_PORT'],
    #         user=settings['MYSQL_USER'],
    #         passwd=settings['MYSQL_PASSWD'],
    #         charset='utf8',  # 编码要加上，否则可能出现中文乱码问题
    #         # 游标设置
    #         cursorclass=pymysql.cursors.DictCursor,
    #         use_unicode=False,
    #     )
    #
    #     dbpool = adbapi.ConnectionPool('pymysql', **dbparams)
    #     return cls(dbpool)


    def process_item(self,item,spider):
        # 使用Twisted异步的将Item数据插入数据库
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error)


    def do_insert(self,cursor,item):


        if item["content"] == None or item["content"] == "":
            pass
        else:
            # 执行具体的插入语句,不需要commit操作,Twisted会自动进
            sql = "insert into phome_ecms_xinnews_check(id,classid,ttid,onclick,plnum,totaldown," \
                  "newspath,filename,userid,username,firsttitle,isgood,ispic,istop,isqf,ismember," \
                  "isurl,truetime,lastdotime,havehtml,groupid,userfen,titlefont,titleurl,stb,fstb," \
                  "restb,keyboard,title,newstime,titlepic,ftitle,smalltext,diggtop) " \
                  "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," \
                  "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"


            sql2 = "insert into phome_ecms_xinnews_check_data" \
                   "(id,classid,writer,befrom,newstext,keyid,dokey,newstempid,closepl,haveaddfen," \
                   " infotags) " \
                   "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "

            sql3 = "insert ignore into phome_ecms_xinnews_index" \
                  "(classid,checked,newstime,truetime,lastdotime,havehtml,originalurl)" \
                  "values(%s,%s,%s,%s,%s,%s,%s)"

            nums = cursor.execute(sql3,(item["class_id"], item['checked'], item["news_time"],int(time.time()),int(time.time()), item['have_html'],str(item['originalurl'])))
            if nums == 0:
                ccc = "当前数据库中url已经存在:"+item["originalurl"]
                print(ccc)

            else:
                cursor.execute('select last_insert_id() as id')
                id = cursor.fetchone()

                cursor.execute(sql2,(id["id"],item["class_id"], item['writer'], item["news_source"],item["content"],item["keyid"],item["dokey"], item['news_tem_pid'],item['closepl'], item['haveaddfen'], item['infotags']))

                cursor.execute(sql,(id["id"],item["class_id"], item['ttid'],item["click_num"],item['plnum'],item['totaldown'],item['news_path'],str(id["id"]),item["user_id"],item["user_name"], item['first_title'],item['isgood'], item['ispic'],item["istop"],item['is_qf'],item['ismember'], item['isurl'],int(time.time()),int(time.time()),item['have_html'],item['group_id'], item['userfen'], item['titlefont'],item['title_url_z']+str(item['class_id'])+'/'+ str(id["id"]) + '.html', item['stb'],item['fstb'],item['restb'],item['news_keyman'], item['title'],item["news_time"],item['titlepic'],item["ftitle"], item['content_summary'],item['diggtop']))

                aaa = "插入第{}条数据中.....".format(id["id"]) + item["originalurl"]
                print(aaa)
                # log.msg(aaa, level=log.INFO)

    def handle_error(self,failure):
        # 打印异步插入异常
        print(failure,"mysql异常")


class mysql_pipelines(object):
    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host=SQLDB[CONRENT_CONF]["MYSQL_HOST"],
            db=SQLDB[CONRENT_CONF]["MYSQL_DBNAME"],
            user= SQLDB[CONRENT_CONF]["MYSQL_USER"],
            passwd=SQLDB[CONRENT_CONF]["MYSQL_PASSWD"],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True)

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        try:
            if item["content"] == None or item["content"] == "" or item["news_time"] == None:
                pass
            else:
                # 执行具体的插入语句,不需要commit操作,Twisted会自动进
                sql = "insert into phome_ecms_xinnews_check(id,classid,ttid,onclick,plnum,totaldown," \
                      "newspath,filename,userid,username,firsttitle,isgood,ispic,istop,isqf,ismember," \
                      "isurl,truetime,lastdotime,havehtml,groupid,userfen,titlefont,titleurl,stb,fstb," \
                      "restb,keyboard,title,newstime,titlepic,ftitle,smalltext,diggtop) " \
                      "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," \
                      "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                sql2 = "insert into phome_ecms_xinnews_check_data" \
                       "(id,classid,writer,befrom,newstext,keyid,dokey,newstempid,closepl,haveaddfen," \
                       " infotags) " \
                       "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "

                sql3 = "insert ignore into phome_ecms_xinnews_index" \
                       "(classid,checked,newstime,truetime,lastdotime,havehtml,originalurl)" \
                       "values(%s,%s,%s,%s,%s,%s,%s)"

                nums = self.cursor.execute(sql3, (
                item["class_id"], item['checked'], item["news_time"], int(time.time()), int(time.time()),
                item['have_html'], str(item['originalurl'])))
                if nums == 0:
                    ccc = "当前数据库中url已经存在:" + item["originalurl"]
                    print(ccc)

                else:
                    self.cursor.execute('select last_insert_id() as id')
                    id = self.cursor.fetchone()

                    self.cursor.execute(sql2, (
                    id["id"], item["class_id"], item['writer'], item["news_source"], item["content"], item["keyid"],
                    item["dokey"], item['news_tem_pid'], item['closepl'], item['haveaddfen'], item['infotags']))

                    self.cursor.execute(sql, (
                    id["id"], item["class_id"], item['ttid'], item["click_num"], item['plnum'], item['totaldown'],
                    item['news_path'], str(id["id"]), item["user_id"], item["user_name"], item['first_title'],
                    item['isgood'], item['ispic'], item["istop"], item['is_qf'], item['ismember'], item['isurl'],
                    int(time.time()), int(time.time()), item['have_html'], item['group_id'], item['userfen'],
                    item['titlefont'], item['title_url_z'] + str(item['class_id']) + '/' + str(id["id"]) + '.html',
                    item['stb'], item['fstb'], item['restb'], item['news_keyman'], item['title'], item["news_time"],
                    item['titlepic'], item["ftitle"], item['content_summary'], item['diggtop']))

                    aaa = "插入第{}条数据中.....".format(id["id"]) + item["originalurl"]
                    print(aaa)
                    # log.msg(aaa, level=log.INFO)
        except Exception as error:
            # 出现错误时打印错误日志
            print(error)
        # return item


    def close_spider(self,spider):
        # 关闭游标和连接
        self.cursor.close()
        self.connect.close()



