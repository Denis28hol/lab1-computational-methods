# Тести для API оптимального розкрою тканини
import pytest
from api import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'endpoint' in data


def test_calculate_get(client):
    response = client.get(
        '/calculate?roll_length=360&XS=2&S=3&M=5&L=2&XL=1'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'result' in data


def test_calculate_post(client):
    payload = {
        "roll_length": 360,
        "demand": {"XS": 2, "S": 3, "M": 5, "L": 2, "XL": 1},
        "excluded_templates": []
    }
    response = client.post(
        '/calculate',
        json=payload
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'result' in data
    assert 'total_rolls' in data['result']


def test_invalid_roll_length(client):
    response = client.get('/calculate?roll_length=0')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
