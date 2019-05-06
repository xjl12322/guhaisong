# coding:utf-8
import requests
from PublicTools import ParseTools
from pymongo import MongoClient

class VIPTycPage(object):
	def __init__(self):
		self.headers = {
            'Host': 'www.tianyancha.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
            'Accept': '*/*',
            'Referer': 'https://www.tianyancha.com/'}
		self.ParseHelper = ParseTools.ParseHelper ()
		
		self.coll = MongoClient('mongodb://127.0.0.1:27017')['tyc_search_log']['tyc_list_vip_教育培训']
		self.flag = 0
		
	@property
	def is_run(self):
		if self.flag < 15 and self.flag != 0:
			return False
		else:
			return True

	def save_to_mongo(self,item):
		try:
			item['_id'] = item['company_id']
			self.coll.insert(item)
			print('save success',item)
		except Exception as e:
			print('save error',e)

	def load_list_page(self,page,kw,base):
		'''加载天眼查列表页'''
		token = ''
		self.headers['Cookie'] = 'auth_token={};'.format (token)
		api = 'https://www.tianyancha.com/search/p{}?key={}&base={}'.format(page,kw,base)
		try:
			res = requests.get(url=api,headers=self.headers).content.decode('utf-8')
		except Exception as e:
			print('错误',e)
		else:
			items = self.ParseHelper.list_parse (res)
			self.flag = 0
			for item in items:
				item['kw'] = kw
				self.save_to_mongo(item)
				self.flag += 1
			
	def run(self):
		kw = '教育培训'
		# 天眼查所有省份base名称
		base_city = ['bj', 'sh', 'tj', 'cq', 'heb', 'sx', 'nmg', 'ln', 'jl', 'hlj', 'js', 'zj', 'ah', 'fj', 'jx', 'sd',
		        'hen', 'hub', 'hun', 'gd', 'gx', 'sc', 'gz', 'yn', 'han', 'snx', 'gs', 'nx', 'qh', 'xj', 'xz', 'hk','mo', 'tw']
		
		city = ['jx']
		city = ['nanchang']
		# 上一次爬取到江西南昌市，有后续需求，重新爬取

		for base in city:
			for page in range(1,251):
				if self.is_run:
					print('页码',page,base)
					self.load_list_page(page,kw,base)
				else:
					break

	def main(self):
		self.run()
		
if __name__ == '__main__':
	vip = VIPTycPage()
	vip.main()
	