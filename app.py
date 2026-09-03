import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'ton_secret_hyper_securise_pour_jwt'

# 1. CONNEXION ET INITIALISATION DB
def get_db_connection():
    conn = psycopg2.connect(
        host="db",
        database=os.environ.get('DB_NAME', 'postgres'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres')
    )
    return conn

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


# 2. DÉFINITION DU DÉCORATEUR DE SÉCURITÉ (Doit être placé AVANT les routes qui l'utilisent)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token manquant ! L\'accès est refusé.'}), 401
        
        try:
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


# 3. ROUTE DE LOGIN (Génération du JWT)
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

    if user and check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token, 'role': user['role']}), 200

    return jsonify({'message': 'Identifiants incorrects'}), 401

# ROUTE D'INSCRIPTION
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Données incomplètes'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT id FROM users WHERE username = %s', (data['username'],))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'message': 'Ce nom d\'utilisateur est déjà pris.'}), 409
        
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (data['username'], hashed_pw))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Compte créé avec succès ! Vous pouvez vous connecter.'}), 201


# ROUTE DE CHANGEMENT DE MOT DE PASSE
@app.route('/api/change-password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.json
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Données incomplètes'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('SELECT password FROM users WHERE id = %s', (current_user['id'],))
    user_db = cur.fetchone()
    
    if not check_password_hash(user_db['password'], data['current_password']):
        cur.close()
        conn.close()
        return jsonify({'message': 'Mot de passe actuel incorrect.'}), 403
        
    new_hashed_pw = generate_password_hash(data['new_password'], method='pbkdf2:sha256')
    cur.execute('UPDATE users SET password = %s WHERE id = %s', (new_hashed_pw, current_user['id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Mot de passe mis à jour avec succès.'}), 200


# 4. ROUTE SÉCURISÉE DES NOTES (Utilise le décorateur défini plus haut)
@app.route('/api/notes', methods=['POST'])
@token_required
def create_note(current_user):
    data = request.json
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'message': 'Données manquantes'}), 400

    # Nouvelles colonnes avec valeurs par défaut
    priority = data.get('priority', 'P4')
    tags = data.get('tags', '')
    status = data.get('status', 'À faire')

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # On gère l'ajout des colonnes dynamiquement si elles n'existent pas (Astuce DevOps)
    try:
        cur.execute('ALTER TABLE notes ADD COLUMN IF NOT EXISTS priority VARCHAR(10) DEFAULT \'P4\';')
        cur.execute('ALTER TABLE notes ADD COLUMN IF NOT EXISTS tags VARCHAR(255) DEFAULT \'\';')
        conn.commit()
    except Exception as e:
        conn.rollback()

    # Insertion de la nouvelle note
    cur.execute(
        'INSERT INTO notes (title, content, status, user_id, priority, tags) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;',
        (data['title'], data['content'], status, current_user['id'], priority, tags)
    )
    new_note = dict(cur.fetchone())
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(new_note), 201

# 5. ROUTES DE MODIFICATION ET SUPPRESSION (CRUD complet & RBAC)
@app.route('/api/notes/<int:note_id>', methods=['PUT', 'DELETE'])
@token_required
def update_delete_note(current_user, note_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Vérifier si la note existe
    cur.execute('SELECT * FROM notes WHERE id = %s', (note_id,))
    note = cur.fetchone()
    
    if not note:
        cur.close()
        conn.close()
        return jsonify({'message': 'Note introuvable'}), 404
        
    # 2. Logique RBAC : L'utilisateur n'est pas admin ET n'est pas l'auteur de la note
    if current_user['role'] != 'admin' and note['user_id'] != current_user['id']:
        cur.close()
        conn.close()
        return jsonify({'message': 'Accès refusé : vous ne pouvez modifier que vos propres notes.'}), 403

    if request.method == 'PUT':
        data = request.json
        # On met à jour le statut (ex: passer de "À faire" à "Terminé")
        cur.execute(
            'UPDATE notes SET status = %s WHERE id = %s RETURNING *;',
            (data.get('status', note['status']), note_id)
        )
        updated_note = dict(cur.fetchone())
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(updated_note), 200
        
    elif request.method == 'DELETE':
        cur.execute('DELETE FROM notes WHERE id = %s;', (note_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Note supprimée avec succès'}), 200


# ROUTE D'ADMINISTRATION (Liste des utilisateurs)
@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    # Sécurité absolue : on bloque immédiatement si ce n'est pas l'admin
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Accès refusé : privilèges administrateur requis.'}), 403
        
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # On récupère les infos sauf les mots de passe !
    cur.execute('SELECT id, username, role FROM users ORDER BY id ASC;')
    users = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return jsonify(users), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)