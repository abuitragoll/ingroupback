import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/users', methods=['POST'])
def post_user():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    preferences = data.get('preferences', [])
    affiliate = data.get('affiliate')
    
    if preferences and (len(preferences) % 2 != 0 or len(set(preferences)) != len(preferences)):
        return jsonify({'error': 'Invalid preferences'}), 400
    
    payload = {
        'name': name,
        'email': email,
        'preferences': preferences,
        'affiliate': affiliate
    }
    
    response = requests.post('https://invelonjobinterview.herokuapp.com/api/post_test', json=payload)
    
    if response.status_code == 200:
        return jsonify(response.json())
    elif response.status_code == 409:
        return jsonify({'error': 'Duplicated user'}), 409
    else:
        return jsonify({'error': 'Unexpected error from test server'}), 500

    
@app.route('/users', methods=['GET'])
def get_users():
    users = [
        {
            'name': 'Raul',
            'email': 'test@company.com',
            'preferences': ['water', 'coffee'],
            'affiliate': True
        },
        {
            'name': 'Marino',
            'email': 'test2@company.com',
            'preferences': [],
            'affiliate': True
        }
    ]
    return jsonify(users)

if __name__ == '__main__':
    app.run()