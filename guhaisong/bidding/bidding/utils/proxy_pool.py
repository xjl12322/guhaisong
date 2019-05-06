#coding:utf-8
import requests,time

# 代理服务器
proxyHost = "p5.t.16yun.cn"
proxyPort = "6445"

# 代理隧道验证信息
proxyUser = "16EKILSS"
proxyPass = "527342"

proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
    "host": proxyHost,
    "port": proxyPort,
    "user": proxyUser,
    "pass": proxyPass,
}

# 设置 http和https访问都是用HTTP代理

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
