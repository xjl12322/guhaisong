# -*-coding: utf-8-*-

# **************************file desc*****************************
__author__ = 'yushanshan'
# createTime : 2019/7/18 19:54
# desc : this is new py file, please write your desc for this file
# ****************************************************************
from requests_url import getXpath
import requests

Header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36",
}
r = requests.get("http://www.goepe.com/apollo/prodetail-shxilun-6772898.html",headers = Header,verify=False)

html = getXpath(r.text)
html.xpath("")







