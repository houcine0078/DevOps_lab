import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# Connexion au conteneur PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host="db",  # Le nom du service de la base de données dans docker-compose.yml
        database=os.environ.get('DB_NAME', 'postgres'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres')
    )
    return conn

# Création de la table au démarrage
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user'
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'À faire',
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
        );
    ''')
    cur.execute('SELECT COUNT(*) FROM users;')
    if cur.fetchone()[0] == 0:
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        cur.execute(
            'INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
            ('admin', hashed_pw, 'admin')
        )
    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print("Erreur d'initialisation de la base de données :", e)

@app.route('/ping', methods=['GET'])
def ping():
    return {"message": "Le Déploiement Continu fonctionne parfaitement !"}, 200

# Routes complètes avec la base de données
@app.route('/api/notes', methods=['GET', 'POST'])
@token_required
def handle_notes(current_user):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        data = request.json
        # On lie automatiquement la nouvelle note à l'utilisateur connecté
        cur.execute(
            'INSERT INTO notes (title, content, status, user_id) VALUES (%s, %s, %s, %s) RETURNING *;',
            (data['title'], data['content'], data.get('status', 'À faire'), current_user['id'])
        )
        new_note = dict(cur.fetchone())
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(new_note), 201
        
    elif request.method == 'GET':
        # Logique RBAC (Role-Based Access Control)
        if current_user['role'] == 'admin':
            cur.execute('SELECT * FROM notes ORDER BY id ASC;')
        else:
            cur.execute('SELECT * FROM notes WHERE user_id = %s ORDER BY id ASC;', (current_user['id'],))
            
        notes = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(notes), 200

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Le frontend enverra le token sous la forme "Bearer eyJhbGci..."
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token manquant ! L\'accès est refusé.'}), 401
        
        try:
            # Décryptage du token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT * FROM users WHERE id = %s', (data['user_id'],))
            current_user = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            return jsonify({'message': 'Token invalide ou expiré !'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Identifiants manquants'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users WHERE username = %s', (data['username'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    # Vérification du mot de passe crypté
    if user and check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token, 'role': user['role']}), 200

    return jsonify({'message': 'Identifiants incorrects'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)