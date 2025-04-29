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
        json={"email": test_user.email, "password": "password123"} # Usa o email do test_user
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
    # Atualiza email e senha
    response = authorized_client.put(
        "/users/me",
        json={"email": "upd@example.com", "password": "newpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "upd@example.com"

    # Tenta login com credenciais novas (usando o client normal, não o autorizado)
    response_login = client.post(
        "/auth/token",
        data={"username": "upd@example.com", "password": "newpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response_login.status_code == 200
    assert "access_token" in response_login.json()

# Adicione um teste para delete se implementado
# def test_delete_user(authorized_client, test_user, db_session):
#     response = authorized_client.delete("/users/me")
#     assert response.status_code == 200
#     # Verifica se o usuário foi removido do banco
#     deleted_user = db_session.query(User).filter(User.id == test_user.id).first()
#     assert deleted_user is None