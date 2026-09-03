import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Le décorateur @patch dit à Python : "Remplace la vraie fonction get_db_connection par un Mock (une doublure)"
@patch('app.get_db_connection')
def test_create_note(mock_get_db, client):
    """Teste la création d'une note en simulant la base de données."""
    # 1. On configure notre fausse base de données pour qu'elle ne plante pas
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # On simule ce que PostgreSQL est censé nous répondre
    mock_cursor.fetchone.return_value = {
        "id": 1, 
        "title": "Note de test CI", 
        "content": "Ceci est un test automatisé", 
        "status": "À faire"
    }

    # 2. On lance la vraie requête
    response = client.post('/api/notes', json={
        "title": "Note de test CI",
        "content": "Ceci est un test automatisé"
    })
    
    # 3. On vérifie que ça passe
    assert response.status_code in [200, 201]

@patch('app.get_db_connection')
def test_get_notes(mock_get_db, client):
    """Teste si la route GET répond correctement avec une DB simulée."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # On simule une base de données vide
    mock_cursor.fetchall.return_value = []

    response = client.get('/api/notes')
    assert response.status_code == 200