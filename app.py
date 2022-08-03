import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

from random import randrange

import certifi
import config

from pymongo import MongoClient
client = MongoClient("mongodb+srv://mbti:mbti@cluster0.54nhc.mongodb.net/?retryWrites=true&w=majority")
db = client.MBTItube


@app.route('/')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/post')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"username": payload["id"]})
        return render_template('post.html', user_info=user_info)


    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.user.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "nick_name": nickname_receive                               # 이름
    }
    db.user.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.user.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/post', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        keyword_receive = request.form["keyword_give"]
        url_receive = request.form["url_give"]

        post_rist = list(db.post.find({}, {'_id': False}))
        count = len(post_rist) + 1

        doc = {
            "num": count,
            "username": payload["id"],
            "keyword": keyword_receive,
            "url": url_receive
        }
        db.post.insert_one(doc)
        return jsonify({'result': 'success', 'msg': '성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


#좋아요 update 및 count 표기 관련
@app.route('/post/like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # 좋아요 수 변경
        user_info = db.user.find_one({"username": payload["id"]})
        num_receive = request.form["num_give"]
        action_receive = request.form["action_give"]

        doc = {
            "num": num_receive,
            "username": user_info["username"]
        }

        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        count = db.likes.count_documents({"num": num_receive})

        return jsonify({"result": "success", "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


#가장 많이 등록된 keyword 순위 조회
@app.route("/top5", methods=["GET"])
def top5_get():

    count = db.post.aggregate([
        {
            "$group": {
                "_id": "$keyword",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        }
    ])

    return jsonify({"result": "success", "count": list(count)})


#리스트 조회 (+ 좋아요 count / 본인 체크 확인)
@app.route("/post/posting", methods=["GET"])
def post_get():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        post_list = list(db.post.find({}, {'_id': False}).sort('_id', -1))

        for post in post_list:
            post["num"] = str(post["num"])
            post["count_heart"] = db.likes.count_documents({"num": post["num"]})
            post["heart_by_me"] = bool(db.likes.find_one({"num": post["num"], "username": payload["id"]}))
        return jsonify({"result": "success", "posts": post_list})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/post/delete", methods=["GET"])
def post_del():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        return jsonify({"result": "success", "username": username})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)