# coding=utf-8
import json
import requests

# 代理ip接口
api = 'http://piping.mogumiao.com/proxy/api/get_ip_bs?appKey=43ac7262c413469e87cd4c53d5779e2c&count=1&expiryDate=0&format=1&newLine=2'
# 白名单接口
wapi = 'http://www.moguproxy.com/proxy/ip/add?mobile=18106140097&ip='


def get():
    try:
        res = requests.get(url=api).text
        if 'code' in res and 'msg' in res:
            dic = json.loads(res)
            if dic['code'] == '0':
                try:
                    proxies = []
                    for ips in dic['msg']:
                        proxies.append(ips['ip']+':'+ips['port'])
                    # pprint(proxies)
                    return proxies
                except:
                    return None
            else:
                # code状态码不等于0加入白名单
                requests.get(wapi)
                return get()
        else:
            # 没有找到code和msg字段加入白名单
            requests.get(wapi)
            return get()
    except:
        # 访问异常，加入白名单
        requests.get(wapi)
        return get()


if __name__ == '__main__':
    get()
