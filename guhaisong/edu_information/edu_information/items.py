# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class EduInformationItem(scrapy.Item):


    class_name = scrapy.Field()  # 新闻类型分类
    class_id = scrapy.Field()
    click_num = scrapy.Field()  # 点击数或浏览数
    news_keyman = scrapy.Field()  # 新闻关键字
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    istop = scrapy.Field()

    ismember = scrapy.Field()
    userfen = scrapy.Field()
    isgood = scrapy.Field()
    originalurl = scrapy.Field()  # 新闻url链接
    group_id = scrapy.Field()
    plnum = scrapy.Field()
    first_title = scrapy.Field()
    is_qf = scrapy.Field()
    totaldown = scrapy.Field()
    news_time = scrapy.Field()  # 新闻发布时间戳
    have_html = scrapy.Field()
    last_dotime = scrapy.Field()
    content_summary = scrapy.Field()  # 摘要
    diggtop = scrapy.Field()
    stb = scrapy.Field()
    ttid = scrapy.Field()
    ispic = scrapy.Field()
    isurl = scrapy.Field()
    fstb = scrapy.Field()
    restb = scrapy.Field()
    title_url_z = scrapy.Field()  # 新闻url主连接
    news_tem_pid = scrapy.Field()
    title = scrapy.Field()  # 新闻标题

    content = scrapy.Field()  # 新闻内容
    writer = scrapy.Field()  # 作者
    news_source = scrapy.Field()  # 新闻来源
    dokey = scrapy.Field()
    closepl = scrapy.Field()
    haveaddfen = scrapy.Field()
    infotags = scrapy.Field()
    keyid = scrapy.Field()
    checked = scrapy.Field()
    news_path = scrapy.Field()
    titlepic = scrapy.Field()
    ftitle = scrapy.Field()
    filename = scrapy.Field()
    titlefont = scrapy.Field()
    # curent_time = scrapy.Field() #当前时间戳
    # update_time = scrapy.Field()  # 入库当前时间戳
