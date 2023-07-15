import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app, resources={r"/users": {"origins": "https://ingroupfront.onrender.com"}})

# Parsear la URL de conexión
url = "postgres://admin:xqfZ2Mg2xG4rCwnXS473zCQElTcAVnUp@dpg-cip417d9aq0dcpvmlkdg-a.frankfurt-postgres.render.com/ingroup"
result = urlparse(url)

# Obtener los componentes de la URL
user = result.username
password = result.password
host = result.hostname
port = result.port
database = result.path.lstrip("/")

@app.route('/users', methods=['POST'])
def post_user():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    preferences = data.get('preferences', [])
    affiliate = data.get('affiliate')

    if preferences:
        even_count = sum(1 for pref in preferences if pref % 2 == 0)
        odd_count = sum(1 for pref in preferences if pref % 2 != 0)

        if even_count == 0 or odd_count == 0:
            return jsonify({'error': 'Debe haber al menos una preferencia par y una preferencia impar'}), 400
        
        if len(set(preferences)) != len(preferences):
            return jsonify({'error': 'No se permiten preferencias repetidas'}), 400
    
    response = requests.get('https://ingroupback.onrender.com/users')
    
    if response.status_code == 200:
        result = response.json()
        users = result['users']
        for user in users:
            if user['name'] == name or user['email'] == email:
                return jsonify({'error': 'Usuario duplicado'}), 400
            
        # Establecer la conexión
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

        cur = conn.cursor()

        # Recuperamos las preferencias para verificar si alguna de ellas no existe y luego insertarla en la base de datos si es necesario.
        cur.execute('''
            SELECT *
            FROM preferences
        ''')

        result_preferences = cur.fetchall()

        existing_ids = []
        for pref in result_preferences:
            existing_ids.append(pref[0])

        missing_ids = []
        for pref in preferences:
            if pref not in existing_ids:
                missing_ids.append(pref)


        for preference_id in missing_ids:
            query = "INSERT INTO preferences (id, preference) VALUES (%s, %s)"
            values = (preference_id, preference_id)
            cur.execute(query, values)
            conn.commit()
            result_preferences.append([preference_id, preference_id])

        # A continuación, realizamos la inserción del usuario en caso de que no exista en la base de datos.
        query = "INSERT INTO users (name, email, affiliate) VALUES (%s, %s, %s)"
        values = (name, email, affiliate)
        cur.execute(query, values)

        conn.commit()

        cur.execute('SELECT LASTVAL()')
        user_id = cur.fetchone()[0]
        

        # Por último, insertamos las preferencias del usuario en la base de datos.
        for pref in preferences:
            query = "INSERT INTO users_preferences(id_user, id_preference) VALUES (%s, %s)"
            values = (user_id, pref)
            cur.execute(query, values)
            conn.commit()

        name_preferences = []
        for pref in result_preferences:
            if pref[0] in preferences:
                name_preferences.append(pref[1])

        conn.close()

        return {
            'name': name,
            'email': email,
            'preferences': name_preferences,
            'affiliate': affiliate
        }

    else:
        return jsonify({'error': 'Error inesperado del servidor de pruebas'}), 500

    
@app.route('/users', methods=['GET'])
def get_users():
    # Establecer la conexión
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
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

    users = []
    for result in results:
        user = {
            'name': result[0],
            'email': result[1],
            'preferences': result[3],
            'affiliate': result[2]
        }
        users.append(user)
    
    conn.close()

    return jsonify({'users': users})

if __name__ == '__main__':
    app.run()