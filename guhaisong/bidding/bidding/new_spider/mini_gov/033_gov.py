# coding:utf-8
from new_spider.spiders import SpiderMeta
from new_spider import request
from new_spider import storage
import re
from new_spider.conf import gov_033, save_temp_info


class GovBuy (SpiderMeta):
	'''甘肃政府采购网'''
	
	def __init__(self):
		SpiderMeta.__init__(self)
		self.config = gov_033
		self.storage = storage.StorageManage (self.config['db_name'])
		self.cookies = {
		    'yunsuo_session_verify': '3fe15e813e1c08cda06ad476bba26442',
		    'security_session_mid_verify': '9ef04b6272f95fb8a6ffb12cb1fa561e',
		    'JSESSIONID': '1C34C980AA15A055765D2D0E6741E17F.tomcat1',
		}
		self.headers = {
		    'Connection': 'keep-alive',
		    'Upgrade-Insecure-Requests': '1',
		    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
		    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		    'Accept-Encoding': 'gzip, deflate',
		    'Accept-Language': 'zh,zh-CN;q=0.9',
		}
		
	def load_get(self, page):
		try:
			url = 'http://www.gszfcg.gansu.gov.cn/web/doSearchmxarticle.action'
			page = (page-1)*20
			params = {
				'limit': '20',
				'start': str(page),
			}
			proxies = self.proxies
			print(proxies)
			response = request.get (url=url, params=params, headers=self.headers, proxies = proxies,cookies=self.cookies)
		except Exception as e:
			print ('load_get error:{}'.format (e))
		else:
			print(response.text)
			ul_li = self._tostrings (response.content.decode('utf-8'), '//div[@class="mBd"]/ul/li')
			print(ul_li)
			for li in ul_li:
				parse_title = {'key': 'title', 'res': li, 'rule': '//a/text()'}
				self.parse_info (parse_title)
				print(save_temp_info)
			# 	parse_status = {'key': 'status', 'res': li, 'rule': '//span/strong[1]/text()'}
			# 	self.parse_info (parse_status)
			#
			# 	parse_publish_time = {'key': 'publish_date', 'res': li, 'rule': '//span//text()'}
			# 	self.parse_info (parse_publish_time)
			# 	save_temp_info['publish_date'] = re.sub (r'\.', '-', ''.join (
			# 		re.findall (r'(\d{4}\.\d{1,2}\.\d{1,2})', save_temp_info['publish_date'])))
			#
			# 	parse_purchase_company_name = {'key': 'purchase_company_name', 'res': li, 'rule': '//span//text()'}
			# 	self.parse_info (parse_purchase_company_name)
			# 	save_temp_info['purchase_company_name'] = ''.join (
			# 		re.findall (r'采购人：{0,1}(.*?)\|', save_temp_info['purchase_company_name']))
			#
			# 	parse_agency_name = {'key': 'agency_name', 'res': li, 'rule': '//span//text()'}
			# 	self.parse_info (parse_agency_name)
			# 	save_temp_info['agency_name'] = ''.join (
			# 		re.findall (r'代理机构：{0,1}(.*?)\|', save_temp_info['agency_name']))
			#
			# 	parse_detail_url = {'key': 'detail_url', 'res': li, 'rule': '//li/a/@href'}
			# 	self.parse_info (parse_detail_url)
			#
			# 	self.load_get_html (save_temp_info['detail_url'])
	
	def load_get_html(self, url):
		if url == None:
			return
		try:
			response = request.get (url=url, headers=self.headers).content.decode ('utf-8')
		except Exception as e:
			print ('laod_get_html error:{}'.format (e))
		else:
			save_temp_info['content_html'] = ''.join (self._tostrings (response, '//div[@class="vF_detail_main"]'))
			save_temp_info['_id'] = self.hash_to_md5 (url)
			self.storage.save_manage (save_temp_info)
	
	def run(self):
		task_li = [
			{'all_page': 2},
		]
		for task in task_li:
			for page in range (1, task['all_page'] + 1):
				self.load_get (page)
	
	def main(self):
		self.run ()


if __name__ == '__main__':
	gb = GovBuy ()
	gb.main ()





