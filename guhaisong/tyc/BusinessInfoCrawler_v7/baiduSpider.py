# coding=utf-8
import time
import requests
from lxml import etree

baike_url = 'https://baike.baidu.com/search/none?word={}&pn=0&rn=10&enc=utf8'


class bdSpider():
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Host': 'baike.baidu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
        }

    def request(self, url, times=0):
        try:
            res = requests.get(url, headers=self.headers, verify=False, timeout=5)
            res.encoding = 'utf-8'
            return res.text
        except Exception as e:
            print(e)
            return self.request(url, times + 1) if times <= 5 else None

    def parse(self, response):
        if response is None:
            return []
        html = etree.HTML(response)
        results = html.xpath('//dl[@class="search-list"]/dd/a')
        item = []
        for result in results:
            if len(result.xpath('./em')) != 0:
                try:
                    item.append(
                        {'num': results.index(result) + 1,
                         'name': ''.join(result.xpath('.//text()')).strip().replace('_百度百科', '')})
                except Exception as e:
                    print(e)
                if results.index(result) >= 4:
                    break
        return item

    def spider(self, keyword):
        url = baike_url.format(keyword)
        response = self.request(url)
        return {
            'code': '10200',
            'keys': keyword,
            'date': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': self.parse(response)
        }


if __name__ == '__main__':
    start = bdSpider()
    from pprint import pprint

    pprint(start.spider('北京联想'))
