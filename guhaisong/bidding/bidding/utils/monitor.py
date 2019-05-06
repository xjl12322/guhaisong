import requests
import time
import os

class MonitorApi(object):
    def __init__(self,name):
        self.name = name

    def running(self):
        url = 'http://127.0.0.1:5000/add'
        pid = os.getppid()
        print(pid)
        time.sleep(3)
        data = {
            'token': 'chenwei_000000',
            'name': self.name,
            'status': '1',
            'add_num': '0',
            'pid': str(pid),
            'server': '120.77.35.48',
        }
        response = requests.post(url = url, data=data)
        return response.json()

    def stopping(self):
        url = 'http://127.0.0.1:5000/add'
        pid = ''
        data = {
            'token': 'chenwei_000000',
            'name': self.name,
            'status': '0',
            'add_num': '0',
            'pid': pid,
            'server': '120.77.35.48',
        }
        response = requests.post(url = url, data=data)
        return response.json()

    def add(self):
        url = 'http://127.0.0.1:5000/add'
        data = {
            'token': 'chenwei_000000',
            'name': self.name,
            'update_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'status': '1',
            'add_num': '1',

        }
        response = requests.post(url = url, data=data)
        return response.json()


    def run(self):
        pass

    def main(self):
        self.run()

if __name__ == '__main__':
    ma = MonitorApi()
    ma.main()

