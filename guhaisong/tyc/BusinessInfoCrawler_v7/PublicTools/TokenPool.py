# coding:utf-8
import requests
import config

class GetToken(object):
	def __init__(self):
		pass
	
	def get_token(self):
		'''新增获取cookie池'''
		try:
			res = requests.get (config.get_token_api).json ()
			if res['code'] != '10200':
				raise EOFError()
		except:
			print ('获取token账号出错！')
		else:
			token_dic = res['info'][0]
			return token_dic
	
	# 拉黑模块
	def black(self, tel, black, state):
		url = config.add_black_api
		if tel == None:
			print('拉黑电话号码为空！')
			return
		data = {'tel': tel, 'black': black, 'state': state}
		try:
			res = requests.post (url=url, data=data).json ()
		except:
			print (tel, '拉黑出错！')
		else:
			if state == 'robot':
				print ('机器人校验', res)
			else:
				print ('拉黑成功', res)









