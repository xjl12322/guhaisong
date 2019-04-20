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
        os.system("scrapy crawl china_huanqiu_com_article_61")
        os.system("scrapy crawl world_huanqiu_com_article_62")
        os.system("scrapy crawl mil_huanqiu_com_world_65")
        os.system("scrapy crawl finance_huanqiu_com_roll_66")
        os.system("scrapy crawl sports_huanqiu_com_others_zh_67")
        os.system("scrapy crawl ent_huanqiu_com_yuleyaowen_68")
        os.system("scrapy crawl go_huanqiu_com_news_tour_69")
        os.system("scrapy crawl china_huanqiu_com_local_70")
        os.system("scrapy crawl fashion_huanqiu_com_news_72")
        os.system("scrapy crawl auto_huanqiu_com_globalnews_73")
        os.system("scrapy crawl ent_huanqiu_com_star_mingxing - neidi_76")
        os.system("scrapy crawl women_huanqiu_com_news_77")
        os.system("scrapy crawl health_huanqiu_com_health_news_78")
        os.system("scrapy crawl tech_huanqiu_com_original_79")
        os.system("scrapy crawl smart_huanqiu_com_ai_80")
        os.system("scrapy crawl tech_huanqiu_com_aerospace_81")
        os.system("scrapy crawl tech_huanqiu_com_business_82")
        os.system("scrapy crawl tech_huanqiu_com_discovery_83")
        os.system("scrapy crawl tech_huanqiu_com_diginews_84")
        os.system("scrapy crawl tech_huanqiu_com_game_86")
        os.system("scrapy crawl tech_huanqiu_com_fantasy_87")
        os.system("scrapy crawl game_huanqiu_com_cartoon_88")
        os.system("scrapy crawl biz_huanqiu_com_pp_89")
        os.system("scrapy crawl hope_huanqiu_com_huodong_90")
        os.system("scrapy crawl lx_huanqiu_com_lxnews_92")

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

        # execute("scrapy crawl china_huanqiu_com_article_61".split())
        # execute("scrapy crawl world_huanqiu_com_article_62".split())
        # execute("scrapy crawl mil_huanqiu_com_world_65".split())
        # execute("scrapy crawl finance_huanqiu_com_roll_66".split())

        # execute("scrapy crawl sports_huanqiu_com_others_zh_67".split())
        # execute("scrapy crawl ent_huanqiu_com_yuleyaowen_68".split())
        # execute("scrapy crawl go_huanqiu_com_news_tour_69".split())
        # execute("scrapy crawl china_huanqiu_com_local_70".split())
        # execute("scrapy crawl fashion_huanqiu_com_news_72".split())
        # execute("scrapy crawl auto_huanqiu_com_globalnews_73".split())
        # execute("scrapy crawl ent_huanqiu_com_star_mingxing_neidi_76".split())
        # execute("scrapy crawl women_huanqiu_com_news_77".split())
        # execute("scrapy crawl health_huanqiu_com_health_news_78".split())
        # execute("scrapy crawl tech_huanqiu_com_original_79".split())
        # execute("scrapy crawl smart_huanqiu_com_ai_80".split())

        # execute("scrapy crawl tech_huanqiu_com_aerospace_81".split())
        # execute("scrapy crawl tech_huanqiu_com_business_82".split())
        # execute("scrapy crawl tech_huanqiu_com_discovery_83".split())
        # execute("scrapy crawl tech_huanqiu_com_diginews_84".split())
        # execute("scrapy crawl tech_huanqiu_com_game_86".split())
        # execute("scrapy crawl tech_huanqiu_com_fantasy_87".split())
        # execute("scrapy crawl game_huanqiu_com_cartoon_88".split())
        # execute("scrapy crawl biz_huanqiu_com_pp_89".split())
        # execute("scrapy crawl hope_huanqiu_com_huodong_90".split())
        execute("scrapy crawl lx_huanqiu_com_lxnews_92".split())


        pass

