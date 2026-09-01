import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_note(client):
    """Teste la création d'une note (ce qui crée aussi la table dans la base vide)."""
    response = client.post('/notes', json={
        "titre": "Note de test CI",
        "contenu": "Ceci est un test automatisé sur GitHub Actions"
    })
    # Accepte 200 ou 201 comme code de succès selon ta configuration Flask
    assert response.status_code in [200, 201] 

def test_get_notes(client):
    """Teste si la route GET /notes répond correctement après la création."""
    response = client.get('/notes')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0 # On vérifie qu'il y a bien au moins une note
