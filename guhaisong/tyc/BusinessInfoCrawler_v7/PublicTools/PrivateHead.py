# coding=utf-8
from PublicTools.UserAgentTools import UserAgentHelper


class PrivateHead:
    def __init__(self):
        self.UserAgent = UserAgentHelper.UserAgent()

    def SignHead(self):
        return {
            'Host': 'www.cods.org.cn',
            'Accept': '*/*',
            'Origin': 'http://www.cods.org.cn',
            'User-Agent': self.UserAgent.UA(),
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'http://www.cods.org.cn/portal/publish/index.html',
        }

    def TokenHead(self):
        return {
            'Host': 'www.cods.org.cn',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Origin': 'http://www.cods.org.cn',
            'User-Agent': self.UserAgent.UA(),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://www.cods.org.cn/portal/publish/index.html',
        }

    def SearchHead(self):
        return {
            'Host': 'ss.cods.org.cn',
            'Connection': 'close',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.UserAgent.UA(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://ss.cods.org.cn/isearch',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

