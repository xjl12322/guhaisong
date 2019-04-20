#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2017/11/6 20:09"
import urllib3
import requests
from lxml import etree
from retrying import retry


def title_slice(title):
    if title =="":
        return title
    else:
        if len(title) >100:
            title = title[0:99]
            return title
        else:
            return title

def keyman_slice(keyman):
    if keyman =="" or "-" in keyman or '"' in keyman or "'" in keyman:
        keyman = ""
        return keyman
    else:
        keyman = keyman.replace("，",",")
        if len(keyman) >80:
            keyman = keyman[0:79]
            keyman = keyman.split(",")
            for x,v in enumerate(keyman):
                if len(v)>=19:
                    keyman.remove(keyman[x])
            keyman = ",".join(keyman)
            keyman = keyman.strip()
            return keyman
        else:
            return keyman

def writer_slice(writer):
    if writer =="":
        return writer
    else:
        if len(writer) >30:
            writer = writer[0:20]+"......"
            return writer
        else:
            return writer

def summay_slice(summay):
    if summay =="":
        return summay
    else:
        if len(summay) >255:
            summay = summay[0:200]
            return summay
        else:
            return summay
def news_source_slice(news_source):

    if news_source =="":
        return news_source
    else:
        if len(news_source) >60:
            news_source = news_source[0:59]
            return news_source
        else:
            return news_source
@retry(stop_max_attempt_number=3)
def requests_detail_page(url):

    urllib3.disable_warnings()
    header = {
        'USER_AGENT':'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)'
    }


    r = requests.get(url,headers = header,verify=False,timeout= 3)
    r.encoding = "utf-8"
    if r.status_code == 200:
        return r.text
    else:
        return None

if __name__ == "__main__":
    # aa = news_source_slice("123")
    url = 'http://school.aoshu.com/school/sxgl/191263/'
    requests_detail_page(url)