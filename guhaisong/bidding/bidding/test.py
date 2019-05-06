import requests,time
import json
import re

cookies = {
    'JSESSIONID': '1C34C980AA15A055765D2D0E6741E17F.tomcat1',
    'yunsuo_session_verify': 'e756f829fdffb64056db759d4dea77b9',
    'security_session_mid_verify': '472af724ef411807fe8e3847bc59310c',
}


def proxies(retrys=0):
	try:
		proxy = requests.get ('http://10.122.44.109:8082/get').text
		if len (proxy) > 30 or len (proxy) < 6:
			raise EOFError ('代理池错误')
	except:
		time.sleep (1)
		return proxies (retrys + 1) if retrys <= 10 else None
	else:
		proxiess = {'http': 'http://' + proxy, 'https': 'http://' + proxy}
		print (proxiess)
		return proxiess

headers = {
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh,zh-CN;q=0.9',
}

def get_cookies(proxiess):
	url = 'http://www.gszfcg.gansu.gov.cn/?security_verify_data=313932302c31303830'
	try:
		res = requests.get(url,headers=headers,proxies=proxiess,cookies=cookies)
	except Exception as e:
		print('---------------------------3----------------')
	else:
		cookies_str = res.cookies
		yunsuo_session_verify = ''.join(re.findall(r'=(.*?)\s',str(cookies_str))).strip()
		return yunsuo_session_verify


def get_data():
	params = {
	    'limit': 20,
	    'start': 20,
	}
	proxiess = proxies ()
	cookies['yunsuo_session_verify']  = get_cookies(proxiess)
	print(cookies)
	url = 'http://www.gszfcg.gansu.gov.cn/web/doSearchmxarticle.action'
	response = requests.get(url=url, headers=headers, params=params, cookies=cookies,proxies=proxiess)
	
	print(response.text)

# print(get_cookies())
get_data()
