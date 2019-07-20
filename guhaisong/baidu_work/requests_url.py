#!/usr/bin/python3

import requests,logging
from lxml import etree
import urllib3
from requests.packages.urllib3 import HTTPSConnectionPool

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
myHeaderSelf = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36",
}
def getRequests(url, myHeader=myHeaderSelf):
    if str(url).startswith("https"):
        try:
            session = requests.session()
            if (myHeader):
                response = session.get(url, headers=myHeader, verify=False, timeout=8)
            else:
                response = session.get(url, headers=myHeaderSelf, verify=False, timeout=8)
            if response and response.status_code <=303:
                response.encoding = response.apparent_encoding
                return response
            else:
                logging.info("请求百度url:  {}".format(url))
        except Exception as e:
            logging.info("请求异常url:  {}---{}".format(url,e))


    else:
        try:
            session = requests.session()
            if (myHeader):
                response = session.get(url, headers=myHeader, timeout=10)
            else:
                response = session.get(url, headers=myHeaderSelf, timeout=10)
            if (response.status_code >= 400):
                print(Exception(url + "\n" + "status_code:" + str(response.status_code)))
            # raise (Exception(url + "\n" + "status_code:" + str(response.status_code)))
            else:
                response.encoding = response.apparent_encoding
                return response
        except Exception as e:
            print(e.__class__.__name__ + ": ", e)
        # raise (e)


def getXpath(text):
    if (text):
        try:
            soup = etree.HTML(text)
            return soup
        except Exception as e:
            print(" ! ! ! xpath Exception: ", e)
        # raise(e)


def postText(url, data=None, headers=myHeaderSelf):
    session = requests.session()
    if str(url).startswith("https"):
        try:
            response = session.post(url, data=data, verify=False, headers=headers)
        except Exception as e:
            print(" getText Exception: ", e)
            return None
        if (response.status_code >= 400):
            print(Exception(url + "\n" + "status_code:" + str(response.status_code)))
        # raise (Exception(url + "\n" + "status_code:" + str(response.status_code)))
        response.encoding = response.apparent_encoding
        return response
    else:
        try:
            response = session.post(url, data=data, headers=headers)
        except Exception as e:
            print(" getText Exception: ", e)
            return None
        if (response.status_code >= 400):
            print(Exception(url + "\n" + "status_code:" + str(response.status_code)))
        # raise (Exception(url + "\n" + "status_code:" + str(response.status_code)))
        response.encoding = response.apparent_encoding
        return response
