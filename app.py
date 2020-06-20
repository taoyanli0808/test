
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
SECRET = "52.Clover"

config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'tyl.0808',
    'database': 'book',
    'port': 3306,
    'charset': 'utf8'
}


def _is_search(sql):
    """
    # 判断SQL语句是否为查询语句。
    :param sql:
    :return:
    """
    return 'select' in sql


def execute_sql(sql):
    """
    # 执行SQL代码，返回执行结果。
    :param sql:
    :return:
    """
    result = None
    db = pymysql.connect(**config)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        print(sql)
        cursor.execute(sql)
        db.commit()
        if _is_search(sql):
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
    except pymysql.err.InternalError as error:
        print(error)
        db.rollback()
    finally:
        cursor.close()
    db.close()
    return result


def sign(data):
    """
    :param data:
    :return:
    """
    # 提取请求参数里的签名，对请求进行相同方式排序。
    signature = data.pop('signature', None)
    data.setdefault('secret', SECRET)
    keys = sorted(data.keys())
    source = ''.join([key+str(data[key]) for key in keys])

    # secret字段不存入数据库
    data.pop('secret')

    # 如果请求时间超过当前时间60秒或晚于当前时间60秒，
    # 则认为请求异常，判定为抓取请求，验签不通过！
    timestamp = data.pop('timestamp')
    now = time.time()
    if math.fabs(now - timestamp) > 60:
        print("请求时间异常，请同步系统时间！")
        return False

    # 使用md5进行签名计算，如果指纹相同则认为验签通过。
    md5 = hashlib.md5()
    md5.update(source.encode('utf-8'))
    fingerprnt = md5.hexdigest()
    return fingerprnt == signature


@app.route('/api/v1/book/create', methods=['POST'])
def api_v1_book_create():
    data = request.get_json()

    if not sign(data):
        return jsonify({
            'status': 400,
            'message': '接口验签失败，请检查请求参数！',
            'data': {}
        })

    keys = ','.join(data.keys())
    values = "'" + "','".join(list(map(str, data.values()))) + "'"
    sql = "insert into book.book({0}) values({1})".format(keys, values)
    id = execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': 'ok',
        'data': { 'id': id }
    })


@app.route('/api/v1/book/delete', methods=['DELETE'])
def api_v1_book_delete():
    data = request.get_json()

    if 'id' not in data or not data['id']:
        return jsonify({
            'status': 400,
            'message': '缺少需要删除的数据ID',
            'data': {}
        })

    sql = "update book.book set deleted=1 where id='{}'".format(data['id'])
    result = execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': '成功删除数据！',
        'data': result
    })


@app.route('/api/v1/book/update', methods=['PUT'])
def api_v1_book_update():
    data = request.get_json()

    if 'id' not in data or not data['id']:
        return jsonify({
            'status': 400,
            'message': '缺少需要删除的数据ID',
            'data': {}
        })

    _id = data.pop('id')
    content = ",".join([key + "=" + str(val) for key, val in data.items()])

    sql = "update book.book set {} where id='{}'".format(content, _id)
    result = execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': '成功更新数据！',
        'data': result
    })


@app.route('/api/v1/book/search', methods=['GET'])
def api_v1_book_search():
    data = request.values.to_dict()
    # 如果请求不包含翻页参数，默认页码为0，默认返回10条数据。
    page = data['page'] if 'page' in data and data['page'] else 0
    limit = data['limit'] if 'limit' in data and data['limit'] else 10

    # 执行SQL语句查询数据库中的图书数据。
    sql = "select * from book.book where deleted=0 limit {},{}".format(page, limit)
    result = execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': 'ok',
        'data': result
    })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )