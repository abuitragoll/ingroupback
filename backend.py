import requests
from flask import Flask, jsonify, request
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

# Parsear la URL de conexión
url = "postgres://admin:xqfZ2Mg2xG4rCwnXS473zCQElTcAVnUp@dpg-cip417d9aq0dcpvmlkdg-a.frankfurt-postgres.render.com/ingroup"
result = urlparse(url)

# Obtener los componentes de la URL
user = result.username
password = result.password
host = result.hostname
port = result.port
database = result.path.lstrip("/")

# Establecer la conexión
conn = psycopg2.connect(
    host=host,
    port=port,
    database=database,
    user=user,
    password=password
)

@app.route('/users', methods=['POST'])
def post_user():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    preferences = data.get('preferences', [])
    affiliate = data.get('affiliate')
    
    if preferences and (len(preferences) == 0 or len(preferences) % 2 == 1 or len(set(preferences)) != len(preferences)):
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
    cur = conn.cursor()

    cur.execute('''
        SELECT u.name, u.email, u.affiliate, STRING_TO_ARRAY(STRING_AGG(p.preference, ','), ',') AS preferences
        FROM users u
        LEFT JOIN users_preferences up ON up.id_user = u.id
        LEFT JOIN preferences p ON up.id_preference = p.id
        GROUP BY u.id, u.name, u.email, u.affiliate
    ''')

    results = cur.fetchall()

    cur.close()
    conn.close()

    users = []
    for result in results:
        user = {
            'name': result[0],
            'email': result[1],
            'preferences': result[3],
            'affiliate': result[2]
        }
        users.append(user)

    return jsonify({'users': users})

if __name__ == '__main__':
    app.run()