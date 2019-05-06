# coding=utf-8
import requests
import json


def post(key,lock):
    api = 'http://47.104.233.81:8081'
    response = requests.post(
        url=api,
        data=json.dumps(
            {'key': key,
             'lock': lock,
             }
        ),
        timeout=30,
    ).text
    try:
        return json.loads(response)['value']
    except:
        return None


if __name__ == '__main__':
    key = '015d449c'
    lock = '7702.605055待人民币'
    response = post(key,lock)
    print(response)

