import hashlib
import datetime

from pymongo import MongoClient
import certifi

import jwt
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

ca = certifi.where()

client = MongoClient("mongodb+srv://mbti:mbti@cluster0.54nhc.mongodb.net/cluster0?retryWrites=true&w=majority")
db = client.MBTItube

UPLOAD_FOLDER = "../static"
SECRET_KEY = 'mbti'


## 로그인페이지

@app.route('/login')
def login():
    return render_template('login.html')


## 회원가입
@app.route('/api/sign-up', methods=['POST'])
def api_sign_up():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    mbti_receive = request.form['mbti_give']
    user = db.users.find_one({'id': id_receive})
    if user is None:
        db.users.insert_one({'id': id_receive, 'pw': pw_hash, 'mbti': mbti_receive, 'profile_pic_real': "profile_pics/profileex.png"})
        check = 1
    else:
        check = 0
    return jsonify({'result': 'success', 'check': check})


## 로그인
@app.route('/api/log-in', methods=['POST'])
def api_log_in():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    # mbti_receive = request.form['mbti_give']
    result = db.users.find_one({'id': id_receive})
    if result is not None:
        if pw_hash == result['pw']:
            payload = {
                'id': id_receive,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                # 'mbti': mbti_receive
            }
            # 서버에서 실행시 디코딩 필요
            # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            check = 1
            return jsonify({'result': 'success', 'token': token, 'check': check})
        else:
            check = 0
            return jsonify({'result': 'success', 'msg': '비밀번호를 확인해주세요', 'check': check})
    else:
        return jsonify(({'result': 'fail', 'msg': '존재하지 않는 회원입니다.'}))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
