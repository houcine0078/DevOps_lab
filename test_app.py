import os
import pytest
import psycopg2
from app import app

# Cette fonction s'exécute automatiquement avant les tests pour préparer la DB
@pytest.fixture(autouse=True)
def setup_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "notesdb"),
        user=os.getenv("DB_USER", "notesuser"),
        password=os.getenv("DB_PASSWORD", "secret")
    )
    cur = conn.cursor()
    # On crée la table de test avec exactement les mêmes colonnes que ton API
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(255) NOT NULL,
            contenu TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_note(client):
    """Teste la création d'une note."""
    response = client.post('/api/notes', json={
        "title": "Note de test CI",
        "content": "Ceci est un test automatisé"
    })
    assert response.status_code in [200, 201]

def test_get_notes(client):
    """Teste si la route GET répond correctement."""
    response = client.get('/api/notes')
    assert response.status_code == 200
