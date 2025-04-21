import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings
from main import app
import os

# Configurar banco de dados de teste
TEST_DATABASE_URL = "sqlite:///./tests/test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar diretórios de teste
os.makedirs("tests/test_uploads", exist_ok=True)
os.makedirs("tests/test_outputs", exist_ok=True)

@pytest.fixture
def test_db():
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    
    # Override de configurações
    settings.DATABASE_URL = TEST_DATABASE_URL
    settings.UPLOAD_DIR = "tests/test_uploads"
    settings.OUTPUT_DIR = "tests/test_outputs"
    
    # Override da dependência para usar o banco de teste
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield  # Executar testes
    
    # Limpar depois dos testes
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user(test_db):
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=User.get_password_hash("password123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def token(test_user):
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client

@pytest.fixture
def test_video():
    # Caminho para um vídeo de teste
    # Pode ser um vídeo curto colocado na pasta tests/resources
    return "tests/resources/test_video.mp4"