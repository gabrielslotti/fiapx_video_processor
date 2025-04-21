import pytest

def test_create_user(client):
    response = client.post(
        "/users/",
        json={"email": "newuser@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data

def test_create_user_duplicate_email(client, test_user):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_get_current_user(authorized_client):
    response = authorized_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_update_user(authorized_client):
    response = authorized_client.put(
        "/users/me",
        json={"email": "updated@example.com", "password": "newpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    
    # Verify we can login with new credentials
    response = authorized_client.post(
        "/auth/token",
        data={"username": "updated@example.com", "password": "newpassword123"}
    )
    assert response.status_code == 200