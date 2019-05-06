# !/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__title__ = ''
__cuthor__ = 'quyl1' 
__mtime__ = '2019/1/23' 
"""

import requests
from selenium import webdriver
import json
from urllib import  request
import time
import re

class RegisteTianYanCha(object):
    def __init__(self):
        self.reg_url = 'https://www.tianyancha.com/cd/reg.json'

        self.final_list = []  ## 空列表

        # self.RedisHelper = Helper()
        self.headers = {
            'Host': 'www.tianyancha.com',
            'Connection': 'close',
            'Accept': '*/*',
            'Origin': 'https://www.tianyancha.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Content-Type': 'application/json; charset=UTF-8',
            'Referer': 'https://www.tianyancha.com/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'Cookie': 'TYCID=27c7890017ad11e9a01f2978fd1fb13c;',
            'Content-Length': '91',
        }

        # 校验使其发送短信
        self.headers2 = {
            'Host': 'www.tianyancha.com',
            'Connection': 'close',
            'Content-Length': '195',
            'Accept': '*/*',
            'Origin': 'https://www.tianyancha.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Content-Type': 'application/json; charset=UTF-8',
            'Referer': 'https://www.tianyancha.com/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'Cookie': 'TYCID=aec441701a3f11e9b587799406f59ed2;',
        }

        self.header_dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}

        self.token = '01158342e67943ba6c11a1ec7ab51ce6367e10b72401'
        self.itemid = '7344'  # 项目编号
        self.excludeno = '170.171.180'  # 排除号段170_171

        # self.driver = webdriver.Chrome()

    # 极验参数获取
    def get_gt(self, retrys=0):
        headers = {
            'Origin': 'https://www.tianyancha.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': '*/*',
            'Referer': 'https://www.tianyancha.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }

        try:
            response = requests.post('https://www.tianyancha.com/verify/geetest.xhtml', headers=headers, verify=True).json() #返回dict
        except:
            return self.get_gt(retrys + 1) if retrys <= 2 else {'state': 'no'}
        else:
            # print('get_gt() == ' + str(response))
            return response

    # 破解
    def crack(self, retry=0):
        gt_dic = self.get_gt()
        if gt_dic['state'] == 'no':
            # print('获取验证码gt错误！')
            return
        gt_dic = gt_dic['data']
        api = 'http://jiyanapi.c2567.com/shibie?gt={}&challenge={}&referer=https://www.tianyancha.com&user=cbi&pass=cbilenovo@2019&return=json&model={}&format=utf8'
        model = 2 if gt_dic['success'] == 1 else 4 if gt_dic['success'] == 0 else 3

        res_dict = requests.get(url=api.format(gt_dic['gt'], gt_dic['challenge'], model)).content.decode('utf-8') #返回str
        # print("res_dict = " + res_dict)
        try:
            res_dict = eval(res_dict)
        except:
            return
        #
        try:
            if str(res_dict['status']) == 'no':
                return self.crack(retry + 1) if retry <= 3 else {'status': 'no'}
            else:
                # print('破解正常')
                return res_dict
        except Exception as e:
            return self.crack(retry + 1) if retry <= 3 else {'status': 'no'}

    # 往服务器发送验证信息促发发送短信，以便获取注册验证码
    # {"phone":"17772972173","type":"SMS","funtype":0,"challenge":"cef92906e8ffe7f874df3eb52859d6bdhm","validate":"8aa2062a3aaa4e53ca0ececda0ab9c88", "seccode":"8aa2062a3aaa4e53ca0ececda0ab9c88|jordan"}
    # POST /verify/sms.json?p=17610178336 HTTP/1.1
    #
    def trigger_send(self, tel,retry=0):
        tel=str(tel)
        res_dict = self.crack()
        try:
            if str(res_dict['status']) == 'no':
                # print('极验破解错误！')
                return
        except:
            return
        trigger_send_url = 'https://www.tianyancha.com/verify/sms.json?p=' + tel
        time.sleep(2)
        data = {
            "phone": tel,
            "type": "SMS",
            "funtype": 0,
            "challenge": str(res_dict['challenge']),
            "validate": str(res_dict['validate']),
            "seccode": str(res_dict['validate']) + "|jordan"
        }
        response = requests.post(url=trigger_send_url, headers=self.headers2, data=json.dumps(data)).json()
        # print('trigger_send: '+str(response))
        if response['state'] == 'ok':
            # print('触发发短信成功！')
            return response
            # self.RedisHelper.push(name=config.usable_user, value=tel, direct=False)
        else:
            return self.trigger_send(retry + 1) if retry <= 3 else {'state': 'no'}

    # 获取手机号码
    def get_phone(self):
        url = 'http://api.fxhyd.cn/UserInterface.aspx?action=getmobile&token=' + self.token + '&itemid=' + self.itemid + '&excludeno=' + self.excludeno
        mobile1 = request.urlopen(request.Request(url=url, headers=self.header_dict)).read().decode(encoding='utf-8')
        if mobile1.split('|')[0] == 'success':
            mobile1 = mobile1.split('|')[1]
            # print('获取号码是: ' + mobile1)
        else:
            # print('获取TOKEN错误,错误代码' + mobile1)
            mobile1 = ''
        return str(mobile1)

    def release_phone(self, tel):
        tel=str(tel)
        url = 'http://api.fxhyd.cn/UserInterface.aspx?action=release&token=' + self.token + '&itemid=' + self.itemid + '&mobile=' + tel
        RELEASE = request.urlopen(request.Request(url=url, headers=self.header_dict)).read().decode(encoding='utf-8')
        if RELEASE == 'success':
            pass
            # print('号码成功释放')
        else:
            pass
            # print('号码释放失败！')

    def get_msg(self, tel):
        tel=str(tel)
        response=self.trigger_send(tel)
        try:
            if response['state'] == 'no':
                # print('触发发短信失败！')
                self.release_phone(tel)
                return
        except:
            self.release_phone(tel)
            return
        text = ''
        WAIT = 100  # 接受短信时长60s
        url = 'http://api.fxhyd.cn/UserInterface.aspx?action=getsms&token=' + self.token + '&itemid=' + self.itemid + '&mobile=' + tel
        text1 = request.urlopen(request.Request(url=url, headers=self.header_dict)).read().decode(encoding='utf-8')
        TIME1 = time.time()
        TIME2 = time.time()
        ROUND = 1
        while (TIME2 - TIME1) < WAIT and not text1.split('|')[0] == "success":
            time.sleep(5)
            text1 = request.urlopen(request.Request(url=url, headers=self.header_dict)).read().decode(encoding='utf-8')
            TIME2 = time.time()
            ROUND = ROUND + 1

        ROUND = str(ROUND)
        if text1.split('|')[0] == "success":
            text = text1.split('|')[1]
            TIME = str(round(TIME2 - TIME1, 1))
            # print('短信内容是' + text + '\n耗费时长' + TIME + 's,循环数是' + ROUND)
        else:
            pass
            self.release_phone(tel)
            # print('获取短信超时，错误代码是' + text1 + ',循环数是' + ROUND)
        # print('短信验证码是： ' + text)
        return text

    def load_html(self, url):
        # try:
        # self.driver.get(url)
        # self.driver.set_script_timeout(15)
        # time.sleep(1)
        # self.driver.find_element_by_xpath('//a[@class="link-white"]').click()
        # time.sleep(5)
        tel = self.get_phone()
        if tel == '':
            return
        # print(tel)
        # 需要点击免费注册之后才能找到对应的号码输入框
        # tel = '17698097896'
        # self.driver.find_element_by_xpath('//input[@class="input contactphone"]').send_keys(tel)
        # time.sleep(1)
        # self.driver.find_element_by_xpath('//div[@class="input-group-btn btn -lg btn-primary"]').click()
        # time.sleep(1)
        response = self.get_msg(tel)
        # print(response)
        if response == '':
            # print('验证码错误，')
            self.release_phone(tel)
            return
        smsCode=''
        try:
            smsCode = re.findall(r'验证码.*?(\d{6})', response)[0]
        except:
            print('验证码错误，'+str(response))
            self.release_phone(tel)
            return
        # print(smsCode)
        self.release_phone(tel)
        self.reg_tyc(tel, smsCode)

        # except:
        #     pass

    def test(self):
        url = 'https://www.tianyancha.com/'
        for i in range(400):
            self.load_html(url)
        # self.load_html(url)

    def reg_tyc(self, tel, smsCode):
        time.sleep(2)
        data = {
            "mobile": tel,
            "cdpassword": "0192023a7bbd73250516f069df18b500",
            "smsCode": smsCode}
        response = requests.post(url=self.reg_url, headers=self.headers, data=json.dumps(data)).json()
        # print(response)
        if response['state'] == 'ok':
            print('注册成功！ '+str(tel)+'&admin23')
            self.final_list.append(tel)
            pass
            # self.RedisHelper.push(name=config.usable_user, value=tel, direct=False)
        else:
            pass
            # print(tel)

    def run(self):
        self.test()

    def main(self):
        self.run()

    def stop(self):
        self.driver.close()


if __name__ == '__main__':
    registe = RegisteTianYanCha()

    # registe.get_gt()
    # registe.crack()
    # registe.get_msg('13487991834')

    registe.main()
    # print("fina_list"+str(registe.final_list))
    list = registe.final_list
    with open('result.txt', 'a+') as f:
        for i in range(len(registe.final_list)):
            print("num:%s   value:%s" % (i+1, list[i]))
            f.write(list[i]+'&admin23'+'\n')

    # registe.stop()