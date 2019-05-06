# coding:utf-8
import time
import config
from pymongo import MongoClient
from PublicTools import RequestTools
from PublicTools import ParseTools
from PublicTools import MongoHelper
from PublicTools import TokenPool
from datetime import datetime,timedelta
from TycSpider import spider
from pprint import pprint
from tyc_update_parse import parse_detail, parse_year_report, parse_branch
import requests
from six.moves import queue
from threading import Thread

class  TycBranchUpdate(object):
	def __init__(self):
		self.other_headers = {
			'Host': 'www.tianyancha.com',
			'Upgrade-Insecure-Requests': '1',
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
			'Accept': '*/*',
			'Referer': 'https://www.tianyancha.com/',
		}
		
		self.MHelper = MongoHelper.Helper ()
		self.MHelper.client = MongoClient(config.mongo_update_host)[config.mongo_update_db]
		self.request = RequestTools.RequestHelper ()
		
		self.ParseHelper = ParseTools.ParseHelper ()
		
		self.tyc_spider = spider()
		self.tyc_token_api = TokenPool.GetToken()
		
		self._task_queue = queue.Queue(100)
	
		
	def find_update_company(self):
		while True:
			days_time = (datetime.now() - timedelta(days=config.tyc_detail_update_days)).strftime('%Y-%m-%d')
			crawl_days_time1 = (datetime.now() - timedelta(days=(config.tyc_detail_update_days/2))).strftime('%Y-%m-%d')
			data = self.MHelper.select_limit(collection=config.update_parent_new, condition={'$and':[{'update_time':{'$lt':days_time},'crawl_time':{'$lt':crawl_days_time1}}]},limits=100)
			# data = self.MHelper.select_limit(collection=config.update_parent_new, condition={},limits=23)
			for i in data:
				self._task_queue.put(i)
		# return data
		
	def start(self,thead_id):
		while True:
			t1 = time.time()
			task_data = self._task_queue.get()
			_id = task_data['_id']
			update_time = task_data['update_time']
			
			crawl_url = task_data['crawl_url']
			
			token_dic = self.tyc_token_api.get_token ()
			if token_dic == None:
				print('获取token出错')
				continue
			tel,token = token_dic['tel'],token_dic['token']
			if tel == None:
				continue
			
			# token = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzQzODQ3NDU1MSIsImlhdCI6MTU1MTY2ODM4OSwiZXhwIjoxNTY3MjIwMzg5fQ.zlq1dBh4tZkgdAcXCd9zhGriUeKHVMECd9IzpCQtCJoUtgIecV4PK40LQ72JWDMG1iP1iWvETiThJO8vVtx05A'
			# tel = '13438474551'
			# print(thead_id,'-1---------------')
			
			company_id = crawl_url.split('/')[-1]
			res_detail = self.tyc_spider.detail(token,company_id)
			
			if res_detail==None:
				continue
			
			if 'antirobot.tianyancha.com/captcha/verify?return_url=' in res_detail:
				self.tyc_token_api.black (tel=tel, black='Y', state='robot')
				continue
				
			elif '登录/注册' in res_detail:
				self.tyc_token_api.black (tel=tel,black='Y',state='')  # 账号过期，拉黑处理
				continue
				
			if '请输入手机号' in res_detail:
				self.tyc_token_api.black (tel=tel,black='Y',state='')  # 拉黑处理
				continue
				
			if 'Redirecting' in res_detail:
				self.tyc_token_api.black (tel=tel,black='Y',state='')  # 拉黑处理
				continue
				
			# print (thead_id, '-2---------------')
			items = self.ParseHelper.detail_parse (company_id, res_detail)
			detail = parse_detail(items)
			
			update = detail['update_time']
			# print (update_time, '<', update)
		
			if update =='' or update_time == update:
				self.MHelper.update (collection=config.update_parent_new, item={"crawl_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, key=_id)
			else:
				# print (thead_id, '-4---------------')
				res_branch = self.tyc_spider.branch(token,company_id)
				branch = parse_branch(res_branch)
				detail['branch'] = branch
				# print (thead_id, '-5---------------')
				res_year_report = self.tyc_spider.annualreport(tel,token,company_id)
				
				if res_branch== None or res_year_report == None:
					continue
				
				year_report = parse_year_report(res_year_report)
				detail['year_report'] = year_report
				self.MHelper.update(collection=config.update_parent_new, item=detail, key=_id)
				# print (thead_id, '-6---------------')
				print('thead_id',thead_id,'t=',time.time()-t1)
		
	def init(self):
		t1 = Thread(target=self.find_update_company,args=())
		
		t2 = Thread(target=self.start,args=(2,))
		t3 = Thread(target=self.start,args=(3,))
		# t4 = Thread(target=self.start,args=(4,))
		#
		# t5 = Thread(target=self.start,args=(5,))
		# t6 = Thread(target=self.start,args=(6,))
		# t7 = Thread(target=self.start,args=(7,))
		
		t1.start()
		t2.start()
		t3.start()
		# t4.start()
		#
		# t5.start()
		# t6.start()
		# t7.start()
		
		t1.join()
		t2.join()
		t3.join()
		# t4.join()
		# t5.join()
		# t6.join()
		# t7.join()
		
	def run(self):
		self.init ()
		
	def main(self):
		self.run()

if __name__ == '__main__':
	tyc = TycBranchUpdate()
	tyc.main()
