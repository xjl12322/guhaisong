# coding=utf-8
import os
import re
import hashlib
import requests

path = os.path.dirname(__file__)


class Crack:
    def __init__(self):
        self.url = 'http://static.tianyancha.com/fonts-styles/fonts/{}/{}/tyc-num.svg'
        # self.url = 'http://static.tianyancha.com/fonts-styles/fonts/{}/{}/tyc-num.woff'
        self.headers = {'user-agent': 'Opera 7.51 (Win XP) Opera/7.51 (Windows NT 5.1; U) 19 [en]'}
        with open(path + '/fonts_all.dict', 'r', encoding='utf-8') as f:
            self.fonts = eval(f.read())

    def Md5(self, string):
        hl = hashlib.md5()
        hl.update(string.encode(encoding='utf-8'))
        return hl.hexdigest()[8:-8]

    def GetChars(self, response):
        chars = re.findall('<glyph glyph-name="(.*?)"', response)
        return None if len(chars) == 0 else chars[1:]

    def SvgChars(self,string, response):
        svgs = re.findall('<glyph glyph-name="{}" unicode=".*?" d="([\s\S]*?)"'.format(string), response)
        return svgs[0] if len(svgs) != 0 else None

    def CharDecrypt(self, key):
        try:
            response = requests.get(url=self.url.format(key[:2], key), headers=self.headers).text
        except Exception as e:
            return print(e)
        chars, item = self.GetChars(response), {}
        if chars is None:
            return
        for char in chars:
            svgs = self.SvgChars(char, response)
            if svgs is None:
                continue
            # item[char] = self.fonts[self.Md5(svgs)] if self.Md5(svgs) in list(self.fonts.keys()) else char
            if self.Md5 (svgs) in list (self.fonts.keys ()):
                item[char] = self.fonts[self.Md5 (svgs)]
            else:
                item[char] = char
                print ('字体库不存在',char, self.Md5 (svgs),'|' ,svgs)
            
        return item

    def NumDecrypt(self, key):
        try:
            response = requests.get(url=self.url.format(key[:2], key), headers=self.headers).text
            print(response)
        except Exception as e:
            return print(e)
        chars, item = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], {}
        for char in chars:
            svgs = self.SvgChars(char, response)
            print(char,'---->',svgs)
            if svgs is None:
                continue
            item[char] = self.fonts[self.Md5(svgs)] if self.Md5(svgs) in list(self.fonts.keys()) else item[char]
        return item

if __name__ == '__main__':
    start = Crack()
    key = '77446869'
    # start.NumDecrypt(key)
    a = start.CharDecrypt(key)
    print(a)
    
    