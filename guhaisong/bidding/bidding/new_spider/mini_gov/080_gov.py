# coding:utf-8
from new_spider.spiders import SpiderMeta
from new_spider import request
from new_spider import storage
import json
from lxml import etree
import re
from new_spider.conf import gov_080, save_temp_info


class GovBuy (SpiderMeta):
	'''中国政府采购网'''
	
	def __init__(self):
		SpiderMeta.__init__ (self)
		self.config = gov_080
		self.storage = storage.StorageManage (self.config['db_name'])
		self.history_count = 0
		self.headers = {
		    'Host': 'www.hebpr.gov.cn',
		    'Accept': 'application/json, text/javascript, */*; q=0.01',
		    'Origin': 'http://www.hebpr.gov.cn',
		    'X-Requested-With': 'XMLHttpRequest',
		    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
		    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
		    'Accept-Encoding': 'gzip, deflate',
		    'Accept-Language': 'zh,zh-CN;q=0.9',
		    'Connection': 'close',
		    }

		
	def load_get(self, page):
		try:
			url = 'http://www.hebpr.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextDataNew'
			page = (page - 1)*10
			data = {"token": "", "pn": page, "rn": 10, "sdt": "", "edt": "", "wd": "", "inc_wd": "", "exc_wd": "","fields": "title", "cnum": "001;002", "sort": "{\"showdate\":\"0\"}", "ssort": "title", "cl": 200,"terminal": "", "condition": [], "time": "", "highlights": "title", "statistics": "","unionCondition": "", "accuracy": "", "noParticiple": "0", "searchRange": "", "isBusiness": 1}
			
			response = request.post (url=url, data=json.dumps(data), headers=self.headers).json()
		except Exception as e:
			print ('load_get error:{}'.format (e))
		else:
			res_li = response['result']['records']
			for res in res_li:
				self.parse_info()
				save_temp_info['title'] = res['title']
				save_temp_info['status'] = res['categoryname']
				save_temp_info['publish_date'] = res['showdate']
				save_temp_info['detail_url'] = 'http://www.hebpr.gov.cn'+res['linkurl']
				save_temp_info['area_name'] = '河北省-' + res['zhuanzai']
				self.load_get_html (save_temp_info['detail_url'])
	
	def load_get_html(self, url):
		if url == None:
			return
		try:
			response = request.get (url=url, headers=self.headers).content.decode ('utf-8')
		except Exception as e:
			print ('laod_get_html error:{}'.format (e))
		else:
			save_temp_info['content_html'] = ''.join (self._tostrings (response, '//div[@class="ewb-main"]'))
			save_temp_info['_id'] = self.hash_to_md5 (url)
			# print(save_temp_info)
			if save_temp_info['publish_date'] >= self.now_time(last_day=1):
				self.storage.save_manage (save_temp_info)
			else:
				self.history_count += 1
				print(self.history_count)
				
	
	def run(self):
		task_li = [
			{'all_page': 100},
		]
		for task in task_li:
			for page in range (1, task['all_page'] + 1):
				if self.is_running:
					self.load_get (page)
					continue
				else:
					break
	
	def main(self):
		self.run ()

if __name__ == '__main__':
	gb = GovBuy ()
	gb.main ()







