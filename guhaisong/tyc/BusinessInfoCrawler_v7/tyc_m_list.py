# coding:utf-8
import requests
from lxml import etree
from FontCracks import Fonts
import config
from PublicTools import MongoHelper
import time

class TycMobileList(object):
	def __init__(self):
		self.headers = {
			'Connection': 'keep-alive',
			'Cache-Control': 'max-age=0',
			'Upgrade-Insecure-Requests': '1',
			'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh,zh-CN;q=0.9',
		}
		
		self.Fonts = Fonts.Font ()
		self.MHelper = MongoHelper.Helper ()
		
		# self.coll = pymongo.MongoClient('mongodb://10.122.33.93:27017')['codes']['dcg_20190129_tycdeal_remain_tyc']
		
	def parse_list(self, response):
		html = etree.HTML (response)
		secret_key = ''.join (
			html.xpath ('//body[contains(@class,"font-")]/@class')).strip ().replace ('font-', '')
		print (secret_key)
		mapping = self.Fonts.CharDecrypt (key=secret_key)
		
		selectors = html.xpath (
			'//div[contains(@class,"search_result_container")]/div[contains(@class,"new-border-bottom pt5 pb5 ml15 mr15")]')
		items = []
		for selector in selectors:
			item = {}
			# 公司id
			_id = ''.join (selector.xpath (
				'./div[@class="row ml0 mr0"]/div[@class="col-xs-10 search_name pl0 pr0"]/a/@href')).split ('/')[-1]
			item['_id'] = _id
			item['company_id'] = _id
			# 公司名称  company_name
			company_name_str = ''.join (selector.xpath (
				'./div[@class="row ml0 mr0"]/div[@class="col-xs-10 search_name pl0 pr0"]/a//text()')).strip ()
			item['company_name'] = company_name_str if mapping is None else ''.join (
				[mapping[i] if i in mapping.keys () else i for i in company_name_str])
			# 所属城市  site
			item['site'] = ''.join (selector.xpath (
				'./div[@class="row ml0 mr0"]/div[@class="search_base col-xs-2 search_repadding2 text-right c3 mt15"]//text()')).strip ()
			# 法定代表人  legal_person
			item['legal_person'] = ''.join (selector.xpath ('./div//div[contains(text(),"法定代表人")]/a/text()')).strip ()
			# 注册资本  registered_capital
			item['registered_capital'] = ''.join (
				selector.xpath ('./div//div[contains(text(),"注册资本")]/span/text()')).strip ()
			# 注册时间  registered_time
			item['registered_time'] = ''.join (
				selector.xpath ('./div//div[contains(text(),"注册时间")]/span/text()')).strip ()
			# 状态  company_status
			item['company_status'] = ''.join (selector.xpath ('./div//div[contains(text(),"状态")]/span/text()')).strip ()
			item['contact_phone'] = ''
			item['contact_mail'] = ''
			item['short_name'] = ''
			item['history_name'] = ''
			item['credit_code'] = ''
			item['sign_up_code'] = ''
			item['org_code'] = ''
			items.append (item)
		
		return items
		
	def proxies(self,retrys=0):
		try:
			# proxy = requests.get ('http://10.122.44.109:8082/get').text
			proxy = requests.get ('http://10.122.33.93:8082/get').text
			if len(proxy) > 30 or len(proxy) < 6:
				raise EOFError('代理池错误')
		except:
			time.sleep(2)
			return self.proxies(retrys+1) if retrys <=3 else None
		else:
			proxies = {'http':'http://'+proxy,'https':'http://'+proxy}
			return proxies
		
	def load_list(self,kw,retrys=0):
		url = 'https://m.tianyancha.com/search?key={}'.format(kw)
		
		proxies = self.proxies()
		try:
			response = requests.get (url=url,headers=self.headers,proxies=proxies, timeout=5)
		except:
			return self.load_list(kw,retrys+1) if retrys <= 3 else []
		else:
			items = self.parse_list(response.text)
			return items
			
	def run(self,kw):
		# items_li = list(self.coll.find({'keys':kw}).limit(1))
		# if any(items_li):
		# 	items = items_li[0]
		# 	del items['_id']
		# 	return items
		items = self.load_list(kw)
		# 存储
		[self.MHelper.push (
			collection=config.mongo_list_collection, item=item, key=item['company_id']) for item in items]
		return {
			'code': '10200',
			'keys': kw,
			'date': str (time.strftime ('%Y-%m-%d %H:%M:%S')),
			'info': items
		}

	def main(self):
		kw = '广东康业医疗设备有限公司'
		items = self.run(kw)
		print(items)

if __name__ == '__main__':
	tyc_m_list = TycMobileList()
	tyc_m_list.main()
