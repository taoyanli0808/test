
import time
import math
import hashlib

import pymysql

from flask import Flask
from flask import request
from flask import jsonify

from flask_cors import CORS
from pymysql import install_as_MySQLdb

app = Flask(__name__)

install_as_MySQLdb()
CORS(app, supports_credentials=True)
SECRET = "52Clover"

config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'tyl.0808',
    'database': 'book',
    'port': 3306,
    'charset': 'utf8'
}


def execute_sql(sql):
    """
    :param sql:
    :return:
    """
    db = pymysql.connect(**config)
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
    except:
        db.rollback()
    finally:
        cursor.close()
    db.close()


def sign(data):
    """
    :param data:
    :return:
    """
    # 如果请求时间超过当前时间60秒或晚于当前时间60秒，
    # 则认为请求异常，判定为抓取请求，验签不通过！
    timestamp = data.get('timestamp')
    now = time.time()
    if math.fabs(now - timestamp) > 60:
        return False

    # 提取请求参数里的签名，对请求进行相同方式排序。
    signature = data.pop('sign', None)
    data.setdefault('secret', SECRET)
    keys = sorted(data.keys())
    source = ''.join([key+str(data[key]) for key in keys])

    # 使用md5进行签名计算，如果指纹相同则认为验签通过。
    md5 = hashlib.md5()
    md5.update(source)
    fingerprnt = md5.hexdigest()
    return fingerprnt == signature


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/v1/book/create', methods=['POST'])
def api_v1_book_create():
    data = request.get_json()
    if sign(data):
        keys = ','.join(data.keys())
        values = "'" + "','".join(list(map(str, data.values()))) + "'"
        sql = "insert into book.book({0}) values({1})".format(keys, values)
        print(sql)
        execute_sql(sql)
        return jsonify({
            'status': 0,
            'message': 'ok',
            'data': {}
        })
    else:
        return jsonify({
            'status': 400,
            'message': 'signature verification failed!',
            'data': {}
        })


@app.route('/api/v1/book/delete', methods=['DELETE'])
def api_v1_book_delete(): pass


@app.route('/api/v1/book/update', methods=['PUT'])
def api_v1_book_update(): pass


@app.route('/api/v1/book/search', methods=['GET'])
def api_v1_book_search(): pass


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
