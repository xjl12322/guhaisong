# coding:utf-8
from pymongo import MongoClient
from new_spider.conf import MONGODB_CON,MONGODB_DB

class StorageManage(object):
	def __init__(self,db):
		self.conect = MongoClient(MONGODB_CON)[MONGODB_DB][db]
	
	def save_manage(self,data_li):
		try:
			self.conect.insert(data_li)
		except Exception as e:
			print('Sava error',e)
		else:
			print('Sava success',data_li)

