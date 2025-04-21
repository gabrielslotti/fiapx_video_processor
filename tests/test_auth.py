import pytest
from fastapi.testclient import TestClient

def test_login_success(client, test_user):
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "wrong_password"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email or password"}

def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/token",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email or password"}

def test_protected_route_no_token(client):
    response = client.get("/videos/status")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_protected_route_invalid_token(client):
    client.headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/videos/status")
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_protected_route_valid_token(authorized_client):
    response = authorized_client.get("/videos/status")
    assert response.status_code == 200