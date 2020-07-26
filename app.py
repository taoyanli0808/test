
import time
import math
import hashlib

from functools import wraps

import pymysql

from flask import Flask
from flask import session
from flask import request
from flask import jsonify
from flask import make_response

from flask_cors import CORS
from pymysql import install_as_MySQLdb

app = Flask(__name__)

install_as_MySQLdb()
CORS(app, supports_credentials=True)

SECRET = "52.Clover"
app.config['SECRET_KEY'] = SECRET

DATABASE = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'tyl.0808',
    'database': 'book',
    'port': 3306,
    'charset': 'utf8mb4'
}


def __is_search(sql):
    """
    # 判断SQL语句是否为查询语句。
    :param sql:
    :return:
    """
    return 'select' in sql


def __execute_sql(sql):
    """
    # 执行SQL代码，返回执行结果。
    # 如果是查询请求，返回所有查询结果
    # 如果是增、删、改请求则返回对应的ID
    :param sql:
    :return:
    """
    result = None
    db = pymysql.connect(**DATABASE)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        print(sql)
        cursor.execute(sql)
        db.commit()
        if __is_search(sql):
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
    except pymysql.err.InternalError as error:
        db.rollback()
    finally:
        cursor.close()
        db.close()
    return result


def __md5sum(source):
    """
    :param source:
    :return:
    """
    # 使用md5进行签名计算，如果指纹相同则认为验签通过。
    md5 = hashlib.md5()
    md5.update(source.encode('utf-8'))
    return md5.hexdigest()


def login_required(func):
    """
    # 自定义登录装饰器，用于判断用户是否登录。
    # 用户登录后请求接口需要在header增加token。
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers['token']
        if token not in session:
            return jsonify({
                'status': 400,
                'message': '您尚未登录，请先登录！',
                'data': {}
            })
        else:
            return func(*args, **kwargs)
    return wrapper


def check_signature(func):
    """
    # 计算签名是否正确以及请求时间是否正常的装饰器
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        signature = data.pop('signature', None)

        # 提取请求参数里的签名，对请求进行相同方式排序。
        data.setdefault('secret', SECRET)
        keys = sorted(data.keys())
        source = ''.join([key + str(data[key]) for key in keys])

        # 如果请求时间超过当前时间60秒或晚于当前时间60秒，
        # 则认为请求异常，判定为抓取请求，验签不通过！
        time_difference = time.time() - data.pop('timestamp')
        if math.fabs(time_difference) > 60:
            return jsonify({
                'status': 400,
                'message': '时间异常，请同步系统时间！',
                'data': {}
            })

        if signature != __md5sum(source):
            return jsonify({
                'status': 400,
                'message': '接口验签失败，请检查请求参数！',
                'data': {}
            })
        else:
            return func(*args, **kwargs)
    return wrapper


@app.route('/api/v1/user/login', methods=['POST'])
def api_v1_user_login():
    """
    # 模拟用户登录的接口，默认用户名clover，默认密码52.clover。
    # 如果用户名和密码不正确则报错，否则写入session与响应头。
    :return:
    """
    data = request.get_json()

    if 'username' not in data or not data['username']:
        return jsonify({
            'status': 400,
            'message': '登录请求缺少用户名！',
            'data': data
        })

    if 'password' not in data or not data['password']:
        return jsonify({
            'status': 400,
            'message': '登录请求缺少密码！',
            'data': data
        })

    # 判断用户名和密码是否正确。
    if data['username'] != 'clover' or data['password'] != '52.clover':
        return jsonify({
            'status': 400,
            'message': '错误的用户名或密码！',
            'data': data
        })

    # 通过用户名和密码计算md5签名，作为登录token值。
    data.setdefault('time', int(time.time()))
    source = "{username}{password}{time}".format(**data)
    __token = __md5sum(source)

    # 将token存入session，值为用户名、密码和最后登录时间。
    session[__token] = data

    response = make_response(jsonify({
        'status': 0,
        'message': 'ok',
        'data': {}
    }))
    # 将token加入到响应头。
    response.headers["token"] = __token
    # 将token加入到cookie。
    response.set_cookie('token', __token)
    return response


@app.route('/api/v1/book/create', methods=['POST'])
@login_required
@check_signature
def api_v1_book_create():
    data = request.get_json()

    keys = ','.join(data.keys())
    values = "'" + "','".join(list(map(str, data.values()))) + "'"
    sql = "insert into book.book({0}) values({1})".format(keys, values)
    id = __execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': 'ok',
        'data': { 'id': id }
    })


@app.route('/api/v1/book/delete', methods=['DELETE'])
@login_required
@check_signature
def api_v1_book_delete():
    data = request.get_json()

    if 'id' not in data or not data['id']:
        return jsonify({
            'status': 400,
            'message': '缺少需要删除的数据ID',
            'data': {}
        })

    sql = "update book.book set deleted=1 where id='{}'".format(data['id'])
    result = __execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': '成功删除数据！',
        'data': result
    })


@app.route('/api/v1/book/update', methods=['PUT'])
@login_required
@check_signature
def api_v1_book_update():
    data = request.get_json()

    if 'id' not in data or not data['id']:
        return jsonify({
            'status': 400,
            'message': '缺少需要更新的数据ID',
            'data': {}
        })

    _id = data.pop('id')
    content = ",".join([key + "=" + str(val) for key, val in data.items()])

    sql = "update book.book set {} where id='{}'".format(content, _id)
    result = __execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': '成功更新数据！',
        'data': result
    })


@app.route('/api/v1/book/search', methods=['GET'])
@login_required
@check_signature
def api_v1_book_search():
    data = request.values.to_dict()
    # 如果请求不包含翻页参数，默认页码为0，默认返回10条数据。
    page = data['page'] if 'page' in data and data['page'] else 0
    limit = data['limit'] if 'limit' in data and data['limit'] else 10

    # 执行SQL语句查询数据库中的图书数据。
    sql = "select * from book.book where deleted=0 limit {},{}".format(page, limit)
    result = __execute_sql(sql)

    return jsonify({
        'status': 0,
        'message': 'ok',
        'data': result
    })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5050,
        debug=True
    )
