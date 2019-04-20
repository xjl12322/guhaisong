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
    name = "mobile_zol_com_cn_more_3_506_85"
    # allowed_domains = ["eol.cn"]
    start_urls = ["http://mobile.zol.com.cn/more/3_506.shtml"]
    # custom_settings = {"DOWNLOAD_DELAY": 0.3}
    class_id = 85
    num = 0
    items = EduInformationItem()
    flags = True
    page_count = 1
    bf = BloomFilter()
    next_index = ""


    def parse(self, response):

        node_obj = response.xpath('''//ul[contains(@class,"content-list")]/li''')
        if not node_obj:
            print("error_spider",self.name)
        for detail in node_obj:
            url = detail.xpath('div/a/@href').extract_first()
            # new_time = detail.xpath('//ul[@class="ysh-test-list"]/li/p[contains(@class,"tickling")]/text()').extract_first()
            titlepic_image = detail.xpath('''div/a/img/@src''').extract_first()
            # print(titlepic_images)
            if not titlepic_image:
                titlepic_images = detail.xpath('''div/a/img''').extract_first()
                titlepic_image = re.search('''<img.*?onerror="javascript:this\.src=.*?\.src=(.*?\.([Jj][pP][gG]|[Pp][Nn][gG])).*?>''',titlepic_images).group(1)
            url = urljoin(response.url, url)
            if url == None or url =="":
                pass
            else:
                if BL:
                    if self.bf.isContains(url):  # 判断字符串是否存在
                        print('url exists!',url)
                    else:
                        self.bf.insert(url)
                        print("请求详情页：",url)
                        yield scrapy.Request(url,callback=self.parse_detail,meta={"titlepic_image":titlepic_image})
                else:
                    yield scrapy.Request(url, callback=self.parse_detail, meta={"titlepic_image": titlepic_image})

        #
        # # # # 多页

        next_node = response.xpath('''//div[@class="page"]/a[contains(text(),"下一页")]/@href''').extract_first()
        next_page = urljoin(response.url, next_node)
        if next_node and self.num<=10:
            print("请求下页链接：",next_page)
            self.num += 1
            yield scrapy.Request(next_page, callback=self.parse)



    def parse_detail(self,response):

        #标题title
        title =  response.xpath('//h1/text()').extract_first(default="")

        #关键字keyman
        keyman = response.xpath('''//meta[@name="keywords"]/@content''').extract_first(default="")
        if keyman:
            keyman = keyman_slice(keyman)
        else:
            keyman = ""

        if title:

            title = title_slice(title)
            #简介summary
            try:
                summary = response.xpath('//meta[@name="description"]/@content').extract_first(default="")
            except Exception as e:
                summary = ""
            summary = summay_slice(summary)

            titlepic_image = response.meta.get("titlepic_image","")

            index_node = response.xpath('''string(//div[@class="article-aboute"])''').extract_first()
            try:
                time_node = response.xpath('''//div[@class="article-aboute"]/span[@id="pubtime_baidu"]/text()''').extract_first()
                news_time = datetime.datetime.strptime(str(time_node).strip(),"%Y-%m-%d %H:%M:%S")
                news_time = int(time.mktime(news_time.timetuple()))
            except Exception as e:
                print("time",e)
                news_time = None

                # writer作者
            writer = writer_defined
            try:
                writer = response.xpath('''string(//div[@class="article-aboute"]/span[@id="author_baidu"])''').extract_first()
                writer = writer.replace("作者：","")
                writer = writer.strip()
            except Exception as e:
                print(e, "writer")
                writer = writer_defined
            writer = writer_slice(writer)
                # 新闻来源news_source
            news_source = news_source_defined
            try:
                source = response.xpath('''//div[@class="article-aboute"]/span[@id="source_baidu"]/text()''').extract_first()
                source = source.replace("[","").replace("]","")
                source = source.strip()
            except Exception as e:
                print(e, "source")
                source = news_source_defined
            news_source = news_source_slice(source)

            #新闻内容content
            content = response.xpath('//div[@id="article-content"]').extract_first()
            content = content.replace("&nbsp", "")
            content = content.replace("&nbsp;", "")
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
            self.items["titlepic"] = titlepic_image
            self.items["ftitle"] = ftitle
            #
            #
            self.items['filename'] = filename
            self.items['titlefont'] = titlefont
            self.items['title_url_z'] = title_url_z
            self.items['originalurl'] = response.url
            #
            yield self.items
