from functools import wraps
from authlib.jose import jwt
from flask import request, jsonify, current_app, Request
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        success, data = verify_req_retrieve_user_id(request)
        if not success:
            return jsonify({'error': data}), 401
        user_id = data
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return f(user, *args, **kwargs)

    return decorated


def verify_req_retrieve_user_id(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not len(auth_header.split(" ")) > 1:
        return False, 'Invalid Authorization Header'
    webtoken = auth_header.split(' ')[1]
    success, value = verify_token(webtoken, current_app.config['JWT_SECRET'])
    if success:
        return True, value.get('id')
    else:
        return False, value

def verify_token(token, jwt_secret):
    try:
        decoded_token = jwt.decode(token, jwt_secret)
        decoded_token.validate()
        return True, decoded_token  
    except:
        return False, 'Invalid token.'
