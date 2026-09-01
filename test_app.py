import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_notes(client):
    """Teste si la route GET /notes répond correctement."""
    response = client.get('/notes')
    assert response.status_code == 200
    assert isinstance(response.json, list)
