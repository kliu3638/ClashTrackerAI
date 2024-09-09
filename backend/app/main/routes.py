import os
import requests
from collections import defaultdict

from authlib.jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask import jsonify, request, current_app
from sqlalchemy import func

from app import db
from app.main import main
from app.middleware import token_required
from app.models.building import Building, BuildingAccount
from app.models.user import GameAccount, User



GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
COC_TOKEN = os.getenv('COC_TOKEN_HOME')
HEADERS = {
    'authorization': f'Bearer {COC_TOKEN}'
}


@main.route('/google-auth', methods=['POST'])
def google_auth():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not len(auth_header.split(" ")) > 1:
        return jsonify({'error': 'Invalid Authorization header'}), 400
    token = auth_header.split(' ')[1]

    req = google_requests.Request()

    id_info = id_token.verify_oauth2_token(token, req, GOOGLE_CLIENT_ID)

    user_id = id_info['sub']
    
    user = User.query.filter_by(id = user_id).first()

    # we need to check if the user has a username because they could have exited
    # during the middle of the sign-in flow before they set a username.
    # In that case, we still want to treat them as if they are a new user
    first_time_login = not user or not user.username

    if not user:
        user = User(
            user_id=user_id,
            email=id_info['email'],
        )
        db.session.add(user)
        db.session.commit()
    
    header = {'alg': 'HS256'}
    claims = {'id': user.id}
    secret_key = current_app.config["JWT_SECRET"]
    webtoken = jwt.encode(header, claims, secret_key).decode()

    return jsonify({'token': webtoken, 'first_time_login': first_time_login}), 200

@main.route('/username', methods=['PUT'])
@token_required
def set_username(user):
    username = request.get_json().get('username')
    check_user = User.query.filter(func.lower(User.user_username) == func.lower(username)).first()
    if check_user:
        return jsonify({'error': 'Username already taken'}), 400

    # Add username requirements and username filtering
    user.user_username = username
    db.session.commit()
    
    return jsonify({'message': 'Username set successfully'}), 200

@main.route('/account', methods=['POST'])
@token_required
def add_account(user):
    data = request.get_json()
    game_id = data.get('game_id').upper()
    game_token = data.get('game_token')
    # check if user already has account ID and if no account
    
    token_body = {
        'token': game_token
    }

    coc_api_url = f'https://api.clashofclans.com/v1/players/%23{game_id}'

    account_response = requests.get(coc_api_url, headers=HEADERS)
    verification_response = requests.post(coc_api_url+'/verifytoken', json=token_body, headers=HEADERS)
    
    if account_response.status_code == 404:
        return jsonify({'error': f'Invalid player tag: #{game_id}'}), 404
    elif account_response.status_code == 200:
        if verification_response.status_code == 200:
            verification = verification_response.json()
            if verification['status'] == 'ok':
                data = account_response.json()

                existing_account = GameAccount.query.filter_by(game_id=game_id).first()
                if existing_account:
                    return jsonify({'message': 'Account already exists'}), 200

                account = GameAccount(
                    user_id = user.user_id,
                    game_id = game_id,
                    game_username = data['name'],
                    experience = data['expLevel'],
                    townhall = data['townHallLevel']
                )

                db.session.add(account)
                db.session.commit()

                return jsonify({
                    "message": "Account added",
                    'username': account.game_username,
                    'experience': account.experience,
                    'townhall': account.townhall
                }), 201
            
            else:
                return jsonify({'error': 'Invalid API token'}), 404
        else:
            return jsonify({'error': 'Failed to fetch data from the Clash of Clans API while verifying API token'}), 500
    else:
        return jsonify({'error': 'Failed to fetch data from the Clash of Clans API while verifying account'}), 500


@main.route('/account', methods=['PUT'])
@token_required
def update_account(user):
    # refactor add_account and update_account to both rely on a helper function that gets the
    # also need helper function to perform calculations for statistics (on all non-buildings i think?)
    # ADD last update time to account table to ensure updates only every 2 min
    pass


@main.route('/building_levels', methods=['PUT'])
@token_required
def update_building_levels(user):
    data = request.get_json()
    game_id = data.get('game_id')
    buildings = data.get('buildings', [])
    for building in buildings:
        building_id = building.get('building_id')
        table_id = building.get('table_id')
        level = building.get('level')

        # Table_id should be valid for frontend
        # If level is 0, building not built
        building_record = db.session.query(BuildingAccount).get((game_id, building_id, table_id))
        if not building_record:
            building_record = BuildingAccount(
                game_id = game_id,
                building_id = building_id,
                table_id = table_id,
                level = level
            )
            db.session.add(building_record)
        else:
            building_record.level = level
    db.session.commit()

    return jsonify({'message': 'Buildings updated'}), 200

# MIGHT NEED MORE TESTING
@main.route('/building_levels', methods=['GET'])
@token_required
def get_building_levels(user):
    data = request.get_json()
    game_id = data.get('game_id')
    account_buildings = (
        db.session.query(BuildingAccount)
        .filter(BuildingAccount.game_id == game_id)
        .all()
    )

    building_data = defaultdict(list)
    for building in account_buildings:
        building_id = building.building_id
        table_id = building.table_id
        level = building.level

        building_data[building_id].append({"table_id": table_id, "level": level})

    return jsonify(building_data), 200