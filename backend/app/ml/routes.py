import os
import requests

import numpy as np
from boto3 import Session
from flask import jsonify, request
from PIL import Image
from uuid import uuid4

from app import db
from app.middleware import token_required
from app.ml import ml
from app.models.building import Building, BuildingAccount, BuildingMax
from app.models.user import GameAccount


ML_URL = os.getenv('ML_URL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')
EXTENSIONS = {'heic', 'jpeg', 'jpg', 'png'}


@ml.route('/recognize_building', methods=['POST'])
@token_required
def recognize_building(user):
    game_id = request.form.get('game_id')
    building_id = request.form.get('building_id') # shud be 0 for eagle
    table_id = request.form.get('table_id')
    image_file = request.files['image_file']
    

    if not valid_file(image_file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    # convert to jpg first if needed

    account_name, townahll = (
        db.session.query(GameAccount.game_username, GameAccount.townhall)
        .filter(GameAccount.game_id == game_id)
        .first()
    )

    ### NEED some sort of logic for making sure we only try to detect buildings that can be built at current townhall level
    max_possible_level, max_number = (
        db.session.query(BuildingMax.max_level, BuildingMax.max_num)
        .filter(BuildingMax.building_id == building_id, BuildingMax.townhall == townahll)
        .scalar()
    )
    if table_id > max_number:
        return jsonify({'message': 'No building to detect for current townhall'}), 200

    curr_image = Image.open(image_file)
    curr_image = curr_image.resize((512, 512))
    image_array = np.array(curr_image)
    image_array = np.expand_dims(image_array, axis=0)
    input_data = {'instances': image_array.tolist()}

    response = requests.post(ML_URL, json=input_data)

    if response.status_code == 200:
        prediction_result = response.json()
        prediction = prediction_result['predictions']

        # go from one to max level for town hall
        class_probabilities = np.exp(prediction) / np.sum(np.exp(prediction), axis=1, keepdims=True)
        final_prediction = np.argmax(class_probabilities[0][:(max_possible_level)])+1

        building = db.session.query(BuildingAccount).get(game_id, building_id, table_id)
        if not building:
            new_building = BuildingAccount(
                building_id = building_id,
                game_id = game_id,
                level = final_prediction
            )

            db.session.add(new_building)
        else:
            building.level = final_prediction

        db.session.commit()


        building_name = (
            db.session.query(Building.building_name)
            .filter(Building.building_id == building_id)
            .scalar()
        )
        
        return jsonify({
            'account': account_name,
            'building': building_name,
            'level': new_building.level
        }), 200
    
    else:
        return jsonify({'error': 'Machine learning model failed'}), response.status_code


@ml.route('/s3', methods=['POST'])
@token_required
def s3_upload(user):
    building_id = 0 # HARDCODED FOR NOW
    level = request.form.get('level')
    image_file = request.files['image_file']

    if not valid_file(image_file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        session = Session(
            aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_ACCESS_KEY
        )
        s3 = session.resource('s3')
        new_filename = str(building_id) + '/' + str(level) + '/' + uuid4().hex + '.jpg'
        s3.Bucket(S3_BUCKET).upload_fileobj(image_file, new_filename)
    except Exception as e:
        return jsonify({'error': f"S3 upload failed: {e}"}), 500
    
    building_name = (
        db.session.query(Building.building_name)
        .filter(Building.building_id == building_id)
        .scalar()
    )

    return jsonify({
        'building': building_name,
        'level': level
    }), 200
    
    


def valid_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONS