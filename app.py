import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

app = Flask(__name__)

# Fonction utilitaire pour se connecter à la base de données
def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD')
    )

# Initialisation de la base de données (Création de la table)
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(200) NOT NULL,
            contenu TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# 1. Créer une note (POST)
@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'titre' not in data or 'contenu' not in data:
        return jsonify({'error': 'Titre ou contenu manquant'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        'INSERT INTO notes (titre, contenu) VALUES (%s, %s) RETURNING id, titre, contenu, created_at',
        (data['titre'], data['contenu'])
    )
    new_note = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(new_note), 201

# 2. Lister toutes les notes (GET)
@app.route('/notes', methods=['GET'])
def get_notes():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, titre, contenu, created_at FROM notes ORDER BY created_at DESC')
    notes = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(notes), 200

# 3. Lire une note précise (GET /<id>)
@app.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, titre, contenu, created_at FROM notes WHERE id = %s', (note_id,))
    note = cur.fetchone()
    cur.close()
    conn.close()
    
    if note is None:
        return jsonify({'error': 'Note non trouvée'}), 404
        
    return jsonify(note), 200

# 4. Supprimer une note (DELETE /<id>)
@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM notes WHERE id = %s RETURNING id', (note_id,))
    deleted_id = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if deleted_id is None:
        return jsonify({'error': 'Note non trouvée'}), 404
        
    return jsonify({'message': 'Note supprimée avec succès'}), 200

if __name__ == '__main__':
    # Tente d'initialiser la table au démarrage
    try:
        init_db()
        print("Base de données initialisée avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")

    # Lancement du serveur Flask
    port = int(os.environ.get('APP_PORT', 8000))
    app.run(host='0.0.0.0', port=port)
     
@app.route('/ping', methods=['GET'])
def ping():
    return {"message": "Le Déploiement Continu fonctionne parfaitement !"}, 200
