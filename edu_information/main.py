#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2017/11/6 20:09"
from scrapy.cmdline import execute
import os,sys
# print(os.path.abspath(__file__))
# print(os.path.dirname(os.path.abspath(__file__)))
import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

cus = "local"
# cus = "line"

if __name__ == "__main__":
    if cus == "line":

        os.system("scrapy crawl news_eastday_com_gd2008_china_61")
        os.system("scrapy crawl news_eastday_com_gd2008_world_62")
        os.system("scrapy crawl news_eastday_com_gd2008_society_63")
        os.system("scrapy crawl news_eastday_com_eastday_13news_auto_news_zhengfa_64")
        os.system("scrapy crawl news_eastday_com_gd2008_mil_65")
        os.system("scrapy crawl news_eastday_com_gd2008_finance_66")
        os.system("scrapy crawl news_eastday_com_eastday_13news_auto_news_sports_67")
        os.system("scrapy crawl news_eastday_com_eastday_13news_auto_news_enjoy_68")
        os.system("scrapy crawl news_eastday_com_gd2008_city_70")
        os.system("scrapy crawl news_eastday_com_eastday_gd2008_history_71")
        os.system("scrapy crawl mobile_zol_com_cn_more_3_506_85")
        os.system("scrapy crawl ixiumei_com_ent_star_75")
        os.system("scrapy crawl szhouse_szhk_com_ent_zfsx_74")
        os.system("scrapy crawl bm_szhk_com_ent_people_75")

        pass



    else:
        # execute("scrapy crawl news_eastday_com_gd2008_china_61".split())
        # execute("scrapy crawl news_eastday_com_gd2008_world_62".split())
        # execute("scrapy crawl news_eastday_com_gd2008_society_63".split())
        # execute("scrapy crawl news_eastday_com_eastday_13news_auto_news_zhengfa_64".split())
        # execute("scrapy crawl news_eastday_com_gd2008_mil_65".split())
        # execute("scrapy crawl news_eastday_com_gd2008_finance_66".split())
        # execute("scrapy crawl news_eastday_com_eastday_13news_auto_news_sports_67".split())
        # execute("scrapy crawl news_eastday_com_eastday_13news_auto_news_enjoy_68".split())
        # execute("scrapy crawl news_eastday_com_gd2008_city_70".split())
        # execute("scrapy crawl news_eastday_com_eastday_gd2008_history_71".split())
        # execute("scrapy crawl mobile_zol_com_cn_more_3_506_85".split())
        # execute("scrapy crawl ixiumei_com_ent_star_75".split())
        # execute("scrapy crawl szhouse_szhk_com_ent_zfsx_74".split())
        # execute("scrapy crawl bm_szhk_com_ent_people_75".split())
        pass

