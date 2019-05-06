# coding=utf-8
import time
import config
from flask import request
from flask import Flask
from flask_cors import *
from flask import jsonify
from flask import render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from TycSpider import spider
from baiduSpider import bdSpider
from CodeListSpider import CodeApi as CodeListApi
from PublicTools.MongoHelper import Helper as Mhelper
import re

from tyc_m_list import TycMobileList

from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(1)
app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["60 per minute", "1 per second"])
# 跨域设置
CORS(app, supports_credentials=True)
app.config['JSON_AS_ASCII'] = False
# 实例化
TycSpider = spider()
Tyc_mobile = TycMobileList()
BaiduSpider = bdSpider()
CodeSpider = CodeListApi()
MHelper = Mhelper()


# 代码中心工作时间
WorkingTime = [_ for _ in range(802, 1940)]

# 程序锁
# global global_lock
global_lock = True

@app.route('/', methods=['GET'])
@limiter.exempt
def index():
    return render_template('index.html')

# 全局搜索模式    http://0.0.0.0:8081/business?mode=list&kw=搜索关键字
# 精准id搜索模式  http://0.0.0.0:8081/business?mode=detail&kw=搜索内部id
# 分支机构搜索模式 http://0.0.0.0:8081/business?mode=branch&kw=搜索内部id
# 股东信息搜索模式  http://0.0.0.0:8081/business?mode=stockholder&kw=搜索内部id
# 对外投资搜索模式  http://0.0.0.0:8081/business?mode=investment&kw=搜索内部id
# 年报信息搜索模式  http://0.0.0.0:8081/business?mode=annualreport&kw=搜索内部id
@app.route('/business', methods=['GET'])
@limiter.limit("150 per minute")
def business():
    global global_lock
    if global_lock:
        mode = request.args.get('mode')
        kw = request.args.get('kw')
        kw = re.sub(r'\r|\n|\t|\s','',kw)
        if mode is None or kw is None or len(kw) == 0:
            return jsonify({
                'code': '10502',
                'keys': 'error',
                'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': 'error'
            })
        items = []
        # 搜索历史数据库
        if str(kw).isdigit() and mode in ['detail', 'branch', 'stockholder', 'investment', 'annualreport']:
            if mode == 'detail':
                items = MHelper.select(collection=config.mongo_detail_collection, condition={'company_id': str(kw)})
            elif mode == 'branch':
                items = MHelper.select(collection=config.mongo_branch_collection, condition={'parent_id': str(kw)})
            elif mode == 'stockholder':
                items = MHelper.select(collection=config.mongo_stockholder_collection,
                                       condition={'company_id': str(kw)})
            elif mode == 'investment':
                items = MHelper.select(collection=config.mongo_investment_collection,
                                       condition={'investor_id': str(kw)})
            elif mode == 'annualreport':
                items = MHelper.select(collection=config.mongo_annualreport_collection,
                                       condition={'company_id': str(kw)})
                
        if len(items) != 0:
            return jsonify({
                'code': '10200',
                'keys': kw,
                'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
                'info': items
            })
        # executor.submit(CHelper.ProductCookie)
        response = TycSpider.run(mode=mode, keyword=kw)
        # print(response)
        try:
            global_lock = False if response['code'] == '10400' else True
        except Exception as e:
            print(1, e)
        return jsonify(response)
    else:
        return jsonify({
            'code': '10400',
            'keys': 'error',
            'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': []
        })


# 天眼查手机端搜索模式 http://0.0.0.0:8081/m_business?kw=关键词
@app.route('/m_business', methods=['GET'])
@limiter.limit("300 per minute")
def m_business():
    kw = request.args.get('kw')
    kw = re.sub (r'\r|\n|\t|\s', '', kw)
    if kw is None or len(kw) == 0:
        return jsonify({
            'code': '10502',
            'keys': 'error',
            'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': []
        })
    return jsonify(Tyc_mobile.run(kw=kw))


# 百科搜索模式 http://0.0.0.0:8081/baike?kw=关键词
@app.route('/baike', methods=['GET'])
@limiter.limit("1000 per minute")
def baike():
    kw = request.args.get('kw')
    kw = re.sub (r'\r|\n|\t|\s', '', kw)
    if kw is None or len(kw) == 0:
        return jsonify({
            'code': '10502',
            'keys': 'error',
            'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': []
        })
    return jsonify(BaiduSpider.spider(keyword=kw))


# 代码中心列表搜索模式 http://0.0.0.0:8081/code?kw=关键词
@app.route('/code', methods=['GET'])
@limiter.limit("120 per minute")
def CodeCenter():
    if int(time.strftime('%H%M')) not in WorkingTime:
        return jsonify({
            'code': '10400',
            'keys': 'error',
            'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': 'sleeping time'
        })
    kw = request.args.get('kw')
    kw = re.sub (r'\r|\n|\t|\s', '', kw)
    if kw is None or len(kw) == 0:
        return jsonify({
            'code': '10502',
            'keys': 'error',
            'crawl_time': str(time.strftime('%Y-%m-%d %H:%M:%S')),
            'info': 'error'
        })
    return jsonify(CodeSpider.run(keyword=kw))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8081,
        debug=True
    )
