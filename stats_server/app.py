import json
import os
import subprocess
import time
import uuid

from werkzeug.utils import secure_filename


from flask import Flask, jsonify, request, abort, Response, send_file, make_response
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from src.config import IMG_PATH, PDF_PATH
from src.models import db, User, Stats
from src.util import pwd_enc, validate_image, request_report_gen


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config['JWT_SECRET_KEY'] = 'my_super_secret_jwt_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False


db.init_app(app)

with app.app_context():
    db.create_all()


jwt = JWTManager(app)


def check_access(user_id):
    if get_jwt_identity() != user_id:
        abort(403)

# dict can be passed through json field else through file


def get_data():
    # dict can be passed through json field else through file
    data = request.json
    if data:
        return data
    data = request.form.get('json')
    if data:
        return json.loads(data)
    return {}


def image_handler():
    # image is passed only through file
    avatar = request.files.get('avatar', None)

    if avatar is None:
        return None
    UPLOAD_EXTENSIONS = ('.jpg', '.png', '.jpeg', '.bmp')

    filename = secure_filename(avatar.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in UPLOAD_EXTENSIONS or \
                validate_image(avatar.stream) is None:
            abort(400, description="Invalid image")

        filename = str(uuid.uuid4()) + file_ext
        avatar.save(IMG_PATH / filename)
        return filename


def handle_params(data):
    password = data.get('password', None)
    if password is not None:
        data['password'] = pwd_enc(password)
    avatar = image_handler()
    if avatar is not None:
        data['avatar'] = avatar
    elif 'avatar' in data:
        data.pop('avatar')


@app.route('/users', methods=['POST'])
def register():
    data = get_data()
    username = data.get('username', None)
    password = data.get('password', None)

    if not username or not password:
        return 'No username or password', 400

    handle_params(data)

    new_user = User()
    new_user.Stats = Stats()

    try:
        new_user.safe_update(data)
    except IntegrityError:
        avatar_path = data.get('avatar', None)
        if avatar_path:
            (IMG_PATH / avatar_path).unlink()
        return 'User already exists', 400

    result = {'user': new_user.to_dict(
    ), 'token': create_access_token(identity=new_user.id)}
    return jsonify(result)


@app.route('/login', methods=['POST'])
def login():
    data = get_data()
    username = data.get('username', None)
    password = data.get('password', None)

    if not username or not password:
        return 'No username or password', 400

    password = pwd_enc(password)
    user = User.query.filter_by(
        username=username, password=password).first()
    if user is None:
        return 'Bad username or password', 401

    access_token = create_access_token(identity=user.id)
    return jsonify({'token': access_token, 'user': f'/users/{user.id}'}), 200


@app.route('/users/<int:user_id>', methods=['GET'], endpoint='get_user')
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return 'No such user', 404
    return jsonify(user.to_dict())


@app.route('/users/me', methods=['GET'])
@jwt_required()
def get_me():
    return get_user(get_jwt_identity())


@app.route('/users', methods=['GET'])
def get_all_users():
    users = list(map(lambda user: user.to_dict(), User.query.all()))
    return jsonify(users)


@app.route('/users/<int:user_id>', methods=['PUT', 'PATCH', 'DELETE'], endpoint='modify_user')
@jwt_required()
def modify_user(user_id):
    check_access(user_id)
    user = User.query.get(user_id)
    if request.method == 'DELETE':
        print(user.avatar)
        if user.avatar:
            (IMG_PATH / user.avatar).unlink()
        user.delete()
        return Response(status=204)

    data = get_data()
    handle_params(data)
    avatar_path = data.get('avatar', None)
    if avatar_path and user.avatar:
        (IMG_PATH / user.avatar).unlink()
    user.safe_update(data)
    return get_user(user_id)


@app.route('/users/<int:user_id>/stats', methods=['GET', 'PUT', 'PATCH'], endpoint='handle_stats')
@jwt_required()
def handle_stats(user_id):
    check_access(user_id)
    user = User.query.get(user_id)
    if request.method == 'GET':
        return jsonify(user.stats.to_dict())

    data = get_data()
    data = {'stats': data}
    user.safe_update(data)
    return jsonify(user.stats.to_dict())


@app.route('/users/<int:user_id>/pdf', methods=['POST', 'GET'], endpoint='handle_stats_file')
@jwt_required()
def handle_stats_file(user_id):
    check_access(user_id)
    user = User.query.get(user_id)
    if request.method == 'POST':
        request_report_gen(user)
        return jsonify({'url': f'/users/{user_id}/pdf'})
    else:
        try:
            return send_file(PDF_PATH / f'{user_id}.pdf', attachment_filename=f'{user.username}_stats.pdf')
        except FileNotFoundError:
            return 'File not found', 404


if __name__ == '__main__':
    subprocess.Popen(['python3', 'report_generator.py'])
    app.run(host='0.0.0.0')
