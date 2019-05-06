# coding:utf-8
from new_spider.spiders import SpiderMeta
from new_spider import request
from new_spider import storage
from new_spider.conf import save_temp_info, gov_071

import re

class GovBuy (SpiderMeta):
	'''湖南省公共资源交易中心'''
	def __init__(self):
		SpiderMeta.__init__ (self)
		self.config = gov_071
		self.storage = storage.StorageManage(self.config['db_name'])
		self.headers = {
		    'Connection': 'keep-alive',
		    'Cache-Control': 'max-age=0',
		    'Upgrade-Insecure-Requests': '1',
		    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
		    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		    'Accept-Encoding': 'gzip, deflate',
		    'Accept-Language': 'zh,zh-CN;q=0.9',
		}
	
	def load_get_html(self, url):
		if url == None:
			return
		try:
			response = request.get (url=url, headers=self.headers).content.decode ('utf-8')
		except Exception as e:
			print ('laod_get_html error:{}'.format (e))
		else:
			save_temp_info['_id'] = self.hash_to_md5 (url)
			save_temp_info['area_name'] = self.get_area('湖南',save_temp_info['title'])
			save_temp_info['content_html'] = ''.join(self._tostrings(response,'//div[@class="content"]')).strip()
			
			self.storage.save_manage(save_temp_info)
	
	def load_get(self, page):
		try:
			url = 'http://www.hnsggzy.com/queryContent_{}-jygk.jspx'.format(page)
			params = {
				'title': '',
				'origin': '',
				'inDates': '1',
				'channelId': '846',
				'ext': '',
				'beginTime': '',
				'endTime': '',
			}
			response = request.get (url=url, params=params, headers=self.headers).content.decode ('utf-8')
		except Exception as e:
			print ('load_get error:{}'.format (e))
		else:
			ul_li = self._tostrings (response, '//div[@class="article-content"]/ul/li')
			for li in ul_li:
				parse_title = {'key': 'title', 'res': li, 'rule': '//a//text()'}
				self.parse_info (parse_title)
				parse_detail_url = {'key': 'detail_url', 'res': li, 'rule': '//a/@href'}
				self.parse_info (parse_detail_url)
				parse_status = {'key': 'status', 'res': li,'rule': '//div[@class="article-list3-t2"]/div[contains(text(),"信息类型")]/text()'}
				self.parse_info (parse_status)
				save_temp_info['status'] = re.sub(r'信息类型|：','',save_temp_info['status'])
				parse_publish_time = {'key': 'publish_date', 'res': li, 'rule': '//div[@class="list-times"]//text()'}
				self.parse_info (parse_publish_time)
				
				self.load_get_html (save_temp_info['detail_url'])
	
	def run(self):
		task_li = [
			{'all_page': 10},
		]
		for task in task_li:
			for page in range (1, task['all_page'] + 1):
				self.load_get (page)
	
	def main(self):
		self.run ()

if __name__ == '__main__':
	gb = GovBuy ()
	gb.main ()

