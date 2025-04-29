# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.core.config import settings
from main import app
from app.models.user import User
from app.core.security import create_access_token
from unittest.mock import MagicMock


# Banco de teste em SQLite
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

@pytest.fixture(autouse=True)
def mock_gcs_client(mocker):
    """Mocks the google.cloud.storage.Client to prevent real calls."""
    # Mocka o cliente GCS para que nenhuma conexão real seja feita
    mock_client_instance = MagicMock()
    # Configura mocks para os métodos do blob se necessário
    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "http://mock-gcs-signed-url.com/test.zip"
    mock_client_instance.bucket.return_value.blob.return_value = mock_blob

    mocker.patch('google.cloud.storage.Client', return_value=mock_client_instance)
    yield mock_client_instance

@pytest.fixture(scope="session", autouse=True)
def init_test_env():
    # Define valores padrão para as configurações ausentes ANTES de usar 'settings'
    os.environ['SMTP_USER'] = 'test@example.com'
    os.environ['SMTP_PASSWORD'] = 'testpassword'
    os.environ['GCS_BUCKET_NAME'] = 'test-bucket'
    # Adicione outras variáveis obrigatórias aqui se necessário

    # Override das configurações que precisam ser diferentes para testes
    settings.DATABASE_URL = TEST_DATABASE_URL
    settings.UPLOAD_DIR = "test_uploads"
    settings.OUTPUT_DIR = "test_outputs"
    settings.GCS_BUCKET_NAME = 'test-bucket' # Define explicitamente para testes

    # Cria pastas de upload/output (embora não sejam mais usadas diretamente)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    # Cria tabelas usando o Base correto
    Base.metadata.create_all(bind=engine)
    yield
    # Dropa ao final
    Base.metadata.drop_all(bind=engine)
    # Limpa as variáveis de ambiente definidas para os testes
    del os.environ['SMTP_USER']
    del os.environ['SMTP_PASSWORD']
    del os.environ['GCS_BUCKET_NAME']


@pytest.fixture
def db_session(init_test_env):
    """Fornece uma sessão de DB por teste com rollback automático."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# Override global de get_db
@pytest.fixture(autouse=True)
def override_get_db(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass # A sessão é fechada pelo fixture db_session
    app.dependency_overrides[get_db] = _get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        hashed_password=User.get_password_hash("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def token(test_user):
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def authorized_client(client, token):
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

@pytest.fixture
def test_video():
    test_video_path = "tests/resources/test_video.mp4"
    if not os.path.exists(test_video_path):
        os.makedirs(os.path.dirname(test_video_path), exist_ok=True)
        with open(test_video_path, "w") as f:
            f.write("dummy video content")
    return test_video_path