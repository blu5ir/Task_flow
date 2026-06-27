import pytest
from taskflow import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test that the main page loads."""
    response = client.get('/')
    assert response.status_code == 200

def test_add_task(client):
    """Test adding a task."""
    response = client.post('/add', json={'title': 'Test Task', 'priority': 'high'})
    assert response.status_code == 200
    assert response.json['success'] == True
