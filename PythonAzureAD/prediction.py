"""
Routes and views for the flask application.
"""
from flask import Flask, jsonify, request, send_file
from tokenhandler import TokenHandler
from tools import processing
from functools import wraps
import pickle
import json

# A config file held outside the repository folders, or on .gitignore
with open('../config.json', 'r') as f:
    config = json.loads(f.read())

# Our trained model which we will use for predictions
with open('./default.pkl', 'rb') as f:
    proc = pickle.load(f)

app = Flask(__name__)
token_handler = TokenHandler(config['publicKeys'],
                             config['clientId'])


def predict(request):
    if 'text' not in request:
        return {'error': 'Missing field: text'}

    start_path = []
    if 'startPath' in request:
        start_path = request['startPath']

    thresh = 0.8
    if 'threshold' in request:
        thresh = request['threshold']
        if thresh > 1:
            thresh = 1
        elif thresh <= 0:
            thresh = 0.1

    max_sug = 3
    if 'maxSuggestions' in request:
        max_sug = request['maxSuggestions']

    clean = False
    if 'clean' in request:
        clean = request['clean']

    # todo: subject and question ..
    text = request['text']
    try:
        predictions = processing.predict(proc,
                                         text,
                                         max_suggests=max_sug,
                                         threshold=thresh,
                                         start_node_path=start_path,
                                         clean=clean)
        sug_list = list()
        for sug in predictions:
            cat_names = [s[0] for s in sug]
            sug_list.append({"path": cat_names,
                             "pathConfidence": [round(s[1], 3) for s in sug]})

        return {'suggestions': sug_list}
    except Exception as err:
        return {'errors': str(err)}


def authorized(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        if 'Authorization' not in request.headers:
            return jsonify({'error': 'Missing authorization header'}), 401
        try:
            access_token = request.headers['Authorization'].split('Bearer ')[1]
        except:
            return jsonify({'error': 'Syntax error in authorization header'}), 401
        try:
            decoded = token_handler.validate_token(access_token)
        except Exception as e:
            return jsonify({'error': "Token error: " + str(e)}), 401

        return func(*args, **kwargs)

    return check_token


@app.route('/predict', methods=['POST'])
@authorized
def get_suggestions():
    if not request.json:
        return jsonify({'error': 'Content type not json'}), 400
    try:
        return jsonify(predict(request.json)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/', methods=['GET'])
@app.route('/swagger.json', methods=['GET'])
@authorized
def get_swagger():
    return send_file('swagger.json')
