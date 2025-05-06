def test_create_user(client):
    response = client.post(
        "/users/",
        json={"email": "new@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == "new@example.com"

def test_create_user_duplicate(client, test_user):
    response = client.post(
        "/users/",
        json={"email": test_user.email, "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_get_me(authorized_client, test_user):
    response = authorized_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id

def test_update_user(client, authorized_client, test_user):
    response = authorized_client.put(
        "/users/me",
        json={"email": "upd@example.com", "password": "newpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "upd@example.com"

    response_login = client.post(
        "/auth/token",
        data={"username": "upd@example.com", "password": "newpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response_login.status_code == 200
    assert "access_token" in response_login.json()