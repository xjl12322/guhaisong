# coding:utf-8
import requests

def _Request(method, url,params=None, data=None, headers=None, cookies=None,
             timeout=None,allow_redirects=True, proxies=None, verify=None, json=None,retrys=0):
    if timeout == None:
        timeout = 5
    if method == 'get':
        try:
            res = requests.get(url=url, params=params, data=data, headers=headers,
                               cookies=cookies, timeout=timeout, allow_redirects=allow_redirects,
                               proxies=proxies, verify=verify, json=json)
        except:
            print('method = post error')
        else:
            return res

    elif method == 'post':
        try:
            res = requests.post(url=url, params=params, data=data, headers=headers,
                               cookies=cookies, timeout=timeout, allow_redirects=allow_redirects,
                               proxies=proxies, verify=verify, json=json)
        except:
            print('method = post error')
        else:
            return res
    else:
        print('method only get or post not other!')

def get(url, params=None, **kwargs):
    return _Request('get', url, params=params, **kwargs)

def post(url, data=None, json=None, **kwargs):
    return _Request('post', url, data=data, json=json, **kwargs)


