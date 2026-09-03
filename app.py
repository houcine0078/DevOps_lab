import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

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
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'À faire'
        );
    ''')
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
def handle_notes():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        data = request.json
        cur.execute(
            'INSERT INTO notes (title, content, status) VALUES (%s, %s, %s) RETURNING *;',
            (data['title'], data['content'], data.get('status', 'À faire'))
        )
        new_note = dict(cur.fetchone())

        conn.commit()
        cur.close()
        conn.close()
        return jsonify(new_note), 201
        
    elif request.method == 'GET':
        cur.execute('SELECT * FROM notes ORDER BY id ASC;')
        notes = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(notes), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)