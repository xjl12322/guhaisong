# coding=utf-8
import requests

from selenium import webdriver
import time
import re
import json
from PublicTools.RedisHelper import Helper
import config

class RegisteTianYanCha (object):
	def __init__(self):
		self.reg_url = 'https://www.tianyancha.com/cd/reg.json'
		self.RedisHelper = Helper ()
		self.headers = {
			'Host': 'www.tianyancha.com',
			'Connection': 'close',
			'Accept': '*/*',
			'Origin': 'https://www.tianyancha.com',
			'X-Requested-With': 'XMLHttpRequest',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
			'Content-Type': 'application/json; charset=UTF-8',
			'Referer': 'https://www.tianyancha.com/',
			'Accept-Encoding': 'gzip, deflate',
			'Accept-Language': 'zh,zh-CN;q=0.9',
			'Cookie': 'TYCID=aec441701a3f11e9b587799406f59ed2;',
			'Content-Length': '91',
		}
		
		# 登陆
		self._login_url = 'http://kapi.yika66.com:20153/User/login?uName=andychen&pWord=qwer1234&Developer=Developer=AZLoo9GET373V3rPDJEnFw%3d%3d'
		# 获取电话号码
		self._phone_url = 'http://kapi.yika66.com:20153/User/getPhone?ItemId=38552&token={}'
		# 获取验证码
		self._msg_url = 'http://kapi.yika66.com:20153/User/getMessage?token={}&ItemId=38552&Phone={}'
		# 释放号码
		self._release_url = 'http://kapi.yika66.com:20153/User/releasePhone?token={}&phoneList={}-38552;'
		# 退出，每次访问务必退出
		self._exit_url = 'http://kapi.yika66.com:20153/User/exit?token={}'
		
		self._token = ''
		
		self.driver = webdriver.Chrome ()
		
		self.get_token()
	
	def get_token(self):
		try:
			response = requests.get (self._login_url).content.decode ('gb2312')
			token = response.split ('&')[0]
		except Exception as e:
			print ('get_token_error', e)
		else:
			self._token = token
	
	def get_phone(self, retrys=0):
		try:
			response = requests.get (self._phone_url.format (self._token)).content.decode ('gb2312')
			if '过期' in response:
				raise ValueError (response)
		
		except Exception as e:
			print ('get_phone_error', e)
			return self.get_phone(retrys+1) if retrys <= 2 else ''
		else:
			phone = response.split (';')[0]
			return phone
	
	def release_phone(self, phone_num):
		try:
			response = requests.get (self._release_url.format (self._token, phone_num)).content.decode ('gb2312')
			if '过期' in response:
				self.get_token ()
				self.release_phone (phone_num)
		except:
			pass
	
	def exit(self):
		try:
			requests.get (self._exit_url).content.decode ('gb2312')
		except:
			pass
	
	
	def test(self):
		url = 'https://www.tianyancha.com/'
		
	def reg_tyc(self,tel,smsCode):
		time.sleep(2)
		data = {
			"mobile":tel,
			"cdpassword":"0192023a7bbd73250516f069df18b500",
			"smsCode":smsCode}
		response = requests.post(url=self.reg_url, headers=self.headers, data=json.dumps(data)).json()
		print(response)
		if response['state'] == 'ok':
			self.RedisHelper.push (name=config.usable_user, value=tel, direct=False)
		else:
			print(tel)
		
	def run(self):
		# tel = '15338419366'
		# smscode = '217236'
		# tel = '13175705024'
		# smscode = '350019'
		# tel = '18359853954'
		# smscode = '710085'
		# self.reg_tyc(tel,smscode)
		self.test()

	def main(self):
		self.run ()
		
	def stop(self):
		self.driver.close ()


if __name__ == '__main__':
	registe = RegisteTianYanCha ()
	registe.main ()
	registe.stop ()
