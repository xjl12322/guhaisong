# -*- coding: utf-8 -*-
import datetime
import scrapy
from urllib.parse import urljoin
from edu_information.commom.commom_method import summay_slice,title_slice,keyman_slice,writer_slice,news_source_slice,requests_detail_page
import re,time
from edu_information.commom.custom_settings import  *
from edu_information.commom.bloomfilter import BloomFilter,BL
from edu_information.commom.filter import contentfilter
from scrapy.selector import Selector
from ..items import EduInformationItem
class XueqianSpider(scrapy.Spider):
    name = "news_eastday_com_gd2008_world_62"
    allowed_domains = ["news.eastday.com"]
    start_urls = ["http://news.eastday.com/gd2008/world/index.html","http://news.eastday.com/eastday/13news/auto/news/world/index_K32.html"]
    custom_settings = {"DOWNLOAD_DELAY": 0.2}
    class_id = 62
    num = 1
    items = EduInformationItem()
    flags = True
    bf = BloomFilter()
    next_index = ""
    header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept - Encoding": "gzip, deflate",
        "Accept - Language": "zh-CN,zh;q=0.9",
        "Cache - Control": "no - cache",
        # "Connection": "keep - alive",
        "Host": "news.eastday.com",
        "Pragma": "no - cache",
        "Referer": "http://news.eastday.com",
        "Upgrade - Insecure - Requests": 1,
        "User - Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
    }
    def parse(self, response):
        node_obj = response.xpath('''//div[@id="left"]/ul/li|//div[@class="leftsection"]/ul/li''')
        if not node_obj:
            print("error_spider",self.name)
        for detail in node_obj:
            url = detail.xpath('a/@href').extract_first()
            time_node = detail.xpath('span[@class="hui12"]/text()|span[@class="black12 fr text4"]/text()').extract_first(default="").strip()
            url = urljoin(response.url, url)
            if url == None or url =="":
                pass
            else:
                if BL:
                    if self.bf.isContains(url):  # 判断字符串是否存在
                        print('url exists!')
                    else:
                        self.bf.insert(url)
                        print("请求详情页：",url)
                        yield scrapy.Request(url,callback=self.parse_detail,headers=self.header,meta={"time_node":time_node})
                else:
                    yield scrapy.Request(url, callback=self.parse_detail, headers=self.header,
                                         meta={"time_node": time_node})

        # # # 多页
        # next_node = response.xpath('''//div[@class="plist"]/div/a[contains(text(),"下一页")]/@href''').extract_first()
        # if next_node != None:
        #     next_page = urljoin(response.url,next_node)
        #     print("请求下页链接：",next_page)
        #     yield scrapy.Request(next_page, callback=self.parse)

    def parse_detail(self,response):

        #标题title
        title =  response.xpath('//div[@id="biaoti"]/text()').extract_first(default="")
        title = title.strip()
        title = title_slice(title)
        #关键字keyman
        keyman = response.xpath('''//meta[@name="keywords"]/@content''').extract_first(default="")
        if keyman:
            keyman = keyman_slice(keyman)
        else:
            keyman = ""

        if title:
            #简介summary
            try:
                summary = response.xpath('//meta[@name="description"]/@content').extract_first(default="").strip()
                summary = summary.replace("东方网-东方新闻-", "")
            except Exception as e:
                summary = ""
            summary = summay_slice(summary)
            index_node = response.xpath('string(//div[@class="time grey12a fc lh22"]/p[last()])').extract_first()

            try:
                time_node = response.meta.get("time_node","")
                time_node = time_node.replace("/","-")
                news_time = datetime.datetime.strptime(str(time_node).strip(),"%Y-%m-%d %H:%M:%S")
                news_time = int(time.mktime(news_time.timetuple()))
            except Exception as e:
                print(e,"time")
                news_time = None

# '来源:新华社 作者:胡浩 林晖 朱基钗 史竞男 选稿:刘晓晶 '
            #writer作者
            try:
                writer = re.search(r".*?作者:(.*?)选稿:.*?", index_node,re.S).group(1)
                writer = writer.strip()
            except Exception as e:
                print(e,"writer")
                writer = writer_defined
            writer = writer_slice(writer)
            # 新闻来源news_source
            try:
                source = re.search(r".*?来源:(.*?)作者:.*?", index_node,re.S).group(1)
                source = source.strip()
            except Exception as e:
                try:
                    source = re.search(r".*?来源:(.*?)选稿:.*?", index_node, re.S).group(1)
                    source = source.strip()
                except Exception as e:
                    try:
                        source = re.search(r".*?来源:(.*)", index_node, re.S).group(1)
                        source = source.strip()
                    except Exception as e:
                        print(e,"source")
                        source = news_source_defined
            news_source = news_source_slice(source)

            #新闻内容content

            content = response.xpath('//div[@id="zw"]').extract_first()
            content = content.replace("&nbsp;", "")
            content = content.replace("&nbsp", "")
            content = content.replace("&nbsp&nbsp&nbsp&nbsp", "")
            content = content.replace("&amp;", "")
            content = content.replace("nbsp", "")
            content = content.replace("&amp;nbsp", "")
            content  = contentfilter(content)
            self.items["news_keyman"] = keyman
            self.items["title"] = title
            self.items["content"] = content
            self.items['content_summary'] = summary
            self.items['click_num'] = click_num
            self.items['news_time'] = news_time
            self.items['news_source'] = news_source
            self.items['writer'] = writer
            #
            #
            self.items["class_id"] = self.class_id
            self.items["user_id"] = user_id
            self.items["istop"] = istop
            self.items["ismember"] = ismember
            self.items["userfen"] = userfen
            self.items["isgood"] = isgood
            self.items["user_name"] = "admin"
            self.items["group_id"] = group_id
            self.items["plnum"] = plnum
            self.items["first_title"] = first_title
            self.items["is_qf"] = is_qf
            self.items["totaldown"] = totaldown
            self.items["have_html"] = have_html
            self.items["last_dotime"] = int(time.time())
            self.items["diggtop"] = diggtop
            self.items["stb"] = stb
            self.items["ttid"] = ttid
            self.items["ispic"] = ispic
            self.items["isurl"] = isurl
            self.items["fstb"] = fstb
            self.items["restb"] = restb
            self.items["news_tem_pid"] = news_tem_pid
            self.items["dokey"] = dokey
            self.items["closepl"] = closepl
            self.items["haveaddfen"] = haveaddfen
            self.items["infotags"] = keyman
            self.items["checked"] = checked
            self.items["keyid"] = keyid
            self.items["news_path"] = news_path
            self.items["titlepic"] = titlepic
            self.items["ftitle"] = ftitle
            #
            #
            self.items['filename'] = filename
            self.items['titlefont'] = titlefont
            self.items['title_url_z'] = title_url_z
            self.items['originalurl'] = response.url
            #
            yield self.items
