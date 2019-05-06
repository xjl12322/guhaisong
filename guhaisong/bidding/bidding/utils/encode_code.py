import json

import execjs

class EncodeStr(object):
    def __init__(self,strs):
        # strs = 'flag=3&name=ZC_JY&key=4028492d64a7dd8a0164d03f27226a13'
        self.strs = strs

    def get_js(self):
        f = open("utils/urlencode.js", 'r', encoding='UTF-8')
        line = f.readline()
        htmlstr = ''
        while line:
            htmlstr = htmlstr + line
            line = f.readline()
        return htmlstr

    def encodes(self):
        jsstr = self.get_js()
        ctx = execjs.compile(jsstr)
        encodestr = ctx.call('encrypt',self.strs)
        return encodestr

