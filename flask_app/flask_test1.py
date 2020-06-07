from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

@app.route('/')
def running():
    return 'Flask is running!'

@app.route('/hello', methods=['GET','POST'])
def hello():
    message = request.get_json(force=True)
    name = message['name']
    response = {
        'greeting': 'Input query: ' + name
    }
    return jsonify(response)
