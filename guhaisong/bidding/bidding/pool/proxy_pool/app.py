# coding=utf-8
from GetIp import CheckIp
from flask import jsonify
from flask import request
from flask import Flask
from flask import render_template
from flask_cors import *
import threading
import time
import config
import pymysql

app = Flask(__name__)
# 跨域设置
CORS(app, supports_credentials=True)

def start_check_ip():
    cip = CheckIp()
    cip.run()

def init():
    t1 = threading.Thread(target=start_check_ip)
    t1.start()

def update_status(ids, status):
    db = pymysql.connect(host=config.host, user=config.user, password=config.password, db=config.db, port=config.port)
    cursor = db.cursor()
    sql = '''update proxy_pool set status = %s where id = %s'''
    try:
        cursor.execute(sql, (status, ids))
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()

def select_ip(time_temp, status):
    db = pymysql.connect(host=config.host, user=config.user, password=config.password, db=config.db, port=config.port)
    cursor = db.cursor()
    sql = '''select * from proxy_pool where time_temp between %s and %s limit 1'''
    try:
        cursor.execute(sql, (time_temp-180000, time_temp))
        results = cursor.fetchall()[0]
        ids = results[0]
        ip = results[1]
    except Exception as e:
        print(e)
        ret = {'ip':None, 'status':'no'}
        return ret
    else:
        update_status(ids, status)
        ret = {'ip':ip, 'status':'ok'}
        return ret
    finally:
        db.close()

@app.route('/proxies', methods=['POST', 'GET'])
def kws():
    init()
    if request.method == 'GET':
        status = int(request.args.get("status"))
        time_temp = int(request.args.get("time_temp"))
        time_temp = 1531811815026
        ret = select_ip(time_temp, status)

        return jsonify(ret)

if __name__ == '__main__':
    app.run(
        # host='0.0.0.0',
        # port='8081',
        debug=False
    )
