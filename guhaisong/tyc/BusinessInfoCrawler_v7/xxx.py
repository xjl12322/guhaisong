import requests


def get_token():
	'''新增获取cookie池'''
	token = requests.get('http://127.0.0.1:8083/get_token').json()
	{'code': '10200', 'date': '2019-02-28 19:38:17', 'info': [{'id': 1, 'tel': '13438474551',
	'token': ''}],
	 'msg': 'ok'}

	