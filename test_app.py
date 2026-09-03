import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# On simule la connexion DB ET le décodage JWT
@patch('app.get_db_connection')
@patch('jwt.decode')
def test_create_note(mock_jwt_decode, mock_get_db, client):
    """Teste la création d'une note en simulant un JWT valide."""
    # 1. On fait croire que le token décodé appartient à l'admin
    mock_jwt_decode.return_value = {'user_id': 1, 'role': 'admin'}
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # 2. side_effect renvoie des résultats différents aux appels successifs de fetchone()
    # - 1er appel (dans @token_required) : trouve l'utilisateur admin
    # - 2ème appel (dans la route POST) : retourne la note tout juste créée
    mock_cursor.fetchone.side_effect = [
        {"id": 1, "username": "admin", "role": "admin"},
        {"id": 1, "title": "Note de test CI", "content": "Test automatisé", "status": "À faire", "user_id": 1}
    ]

    # 3. On envoie la requête avec un faux en-tête d'autorisation
    response = client.post('/api/notes', 
        json={"title": "Note de test CI", "content": "Test automatisé"},
        headers={'Authorization': 'Bearer FAUX_TOKEN_DE_TEST'}
    )
    
    assert response.status_code in [200, 201]


@patch('app.get_db_connection')
@patch('jwt.decode')
def test_get_notes(mock_jwt_decode, mock_get_db, client):
    """Teste la lecture des notes avec un JWT simulé."""
    mock_jwt_decode.return_value = {'user_id': 1, 'role': 'admin'}
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Appel fetchone() dans @token_required : valide l'utilisateur
    mock_cursor.fetchone.return_value = {"id": 1, "username": "admin", "role": "admin"}
    # Appel fetchall() dans la route GET : retourne une liste vide
    mock_cursor.fetchall.return_value = []

    response = client.get('/api/notes', headers={'Authorization': 'Bearer FAUX_TOKEN_DE_TEST'})
    assert response.status_code == 200