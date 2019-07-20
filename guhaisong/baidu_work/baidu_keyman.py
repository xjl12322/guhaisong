#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2017/11/6 20:09"

from urllib.parse import quote
import requests
from lxml import etree
import re
def inquiry(text):
    # text = "商标注册"
    keymans = quote(text)
    domainend = (
        '.com/', '.cn/', '.top/', '.co/', '.info/', '.net/', '.org/', '.xyz', '.mobi/',
        '.cx/', '.red/', 'gov/', 'edu/', '.mil/', '.biz/', '.name/')
    header = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}
    i = 1
    whole_url = []
    domain_name = []

    for page in range(0,20,10):
        print("第{}页".format(page))
        response = requests.get(url="https://www.baidu.com/s?wd={}&pn={}&oq=商标注册".format(keymans,page),headers=header)

        selecter = etree.HTML(response.text)
        if page == 10:
            i = 11
        for x in range(0,10):
            title= selecter.xpath('string(//div[@id="%s"]/h3)' %(x+i)).strip()
            url = selecter.xpath('//div[@id="%s"]/h3/a[1]/@href' %(x+i))[0]
            print(x+i)
            print(title,"lllllllllllllllllllll")
            response1 = requests.get(url=url,headers = header,allow_redirects=False)
            # print(response1.url)
            # print(response1.status_code)
            if response1.status_code == 302:
                url = response1.headers.get("location")
                whole_url.append(url)
                print(url,"uuuuuuuuuuuuuuuuu")
                if url.endswith(domainend):
                    top_domain = re.sub(r"^http://www.|^https://www.|^http://|^https://|^www.|/$", "", url)
                    print(top_domain,"222222222222222222222222")
                    domain_name.append(top_domain)
                    # print(top_domain)

    print("顶级域名/二级数量",len(domain_name))
    print("内容页数量",len(whole_url)-len(domain_name))


if __name__ == "__main__":

    #
    # if len(sys.argv) < 2:
    #     print("请输入关键字")
    # start = time.time()
    # keyman = sys.argv[1]
    # keyman = keyman.strip()
    # inquiry(keyman)
    #
    # end = time.time() - start
    # print(end)

    inquiry("商标注册")
# import sys
#
# a = sys.argv
# print("内容",a)





