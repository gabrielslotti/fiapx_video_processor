# tests/test_videos.py
import pytest
from unittest.mock import patch, MagicMock # Garanta que patch está importado
from fastapi import UploadFile
import io
from app.models.video import Video, VideoStatus

# Mock para a task Celery (mantém como fixture separado ou dentro do teste)
@pytest.fixture
def mock_celery_task():
    # O alvo do patch deve ser onde 'process_video' é importado e chamado com '.delay'
    # Assumindo que é em app.api.videos
    with patch("app.api.videos.process_video.delay") as mock_delay:
        yield mock_delay

# --- Correção Erro 6 ---
# Removido o patch para StorageService
def test_upload_video(authorized_client, mock_celery_task, test_user, db_session, mock_gcs_client): # Adicionado mock_gcs_client
    file_content = b"dummy video file content"
    response = authorized_client.post(
        "/videos/upload",
        files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert data["message"] == "Video upload started"

    # Verifica se o método upload_file do mock GCS (via conftest) foi chamado
    # Acessando através do mock global injetado
    # Acessa o mock do blob retornado pelo mock do bucket
    mock_gcs_client.bucket.return_value.blob.return_value.upload_from_filename.assert_called_once()

    # Verifica se a task Celery foi chamada
    mock_celery_task.assert_called_once()
    args, kwargs = mock_celery_task.call_args
    assert len(args) == 3
    assert args[2] == data["video_id"]

    # Verifica se o vídeo foi salvo no banco
    video_in_db = db_session.query(Video).filter(Video.id == data["video_id"]).first()
    assert video_in_db is not None
    assert video_in_db.filename == "test.mp4"
    assert video_in_db.status == VideoStatus.PENDING
    assert video_in_db.user_id == test_user.id
    assert video_in_db.storage_input.startswith("uploads/")

# test_get_videos_status_empty e test_get_videos_status_after_upload (mantêm como antes)
def test_get_videos_status_empty(authorized_client):
    response = authorized_client.get("/videos/status")
    assert response.status_code == 200
    assert response.json() == []

def test_get_videos_status_after_upload(authorized_client, test_user, db_session):
    video = Video(
        filename="db_test.mp4",
        storage_input="uploads/db_test.mp4",
        status=VideoStatus.PROCESSING,
        user_id=test_user.id
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    response = authorized_client.get("/videos/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == video.id
    assert data[0]["filename"] == "db_test.mp4"
    assert data[0]["status"] == "processing"

# test_secure_download_invalid_token (mantém como antes, mas verifica import em app/api/videos.py)
def test_secure_download_invalid_token(client):
    # Este teste assume que verify_download_token retorna None para tokens inválidos
    # e que o mock global de GCS não interfere aqui.
    # Garanta que verify_download_token está importado em app/api/videos.py
    with patch("app.api.videos.verify_download_token", return_value=None) as mock_verify:
         response = client.get("/videos/secure-download/invalid-token")
         assert response.status_code == 403
         assert "Invalid or expired" in response.json()["detail"]
         mock_verify.assert_called_once_with("invalid-token")


def test_secure_download_success(client, test_user, db_session, mock_gcs_client):
    # Usa 'with patch' com o alvo correto
    with patch("app.api.videos.verify_download_token", return_value=(1, test_user.id)) as mock_verify:
        # Cria um vídeo COMPLETED no banco com ID 1
        video = Video(
            id=1,
            filename="completed.mp4",
            storage_input="uploads/completed.mp4",
            storage_output="outputs/1.zip",
            status=VideoStatus.COMPLETED,
            user_id=test_user.id
        )
        db_session.add(video)
        db_session.flush()
        db_session.commit()

        response = client.get("/videos/secure-download/valid-token-mocked")

        # Verifica se o mock foi chamado
        mock_verify.assert_called_once_with("valid-token-mocked")
        
        # Verifica chamada ao GCS mockado
        mock_gcs_client.bucket.return_value.blob.return_value.generate_signed_url.assert_called_once()

# --- Correção Erro 3 ---
def test_secure_download_video_not_found(client, test_user):
    # Usa 'with patch' com o alvo correto
    with patch("app.api.videos.verify_download_token", return_value=(999, test_user.id)) as mock_verify:
        response = client.get("/videos/secure-download/token-for-nonexistent-video")
        # O endpoint deve retornar 404 se o vídeo não for encontrado após validação do token
        assert response.status_code == 404
        assert "Video not available" in response.json()["detail"]
        # Verifica se o mock foi chamado
        mock_verify.assert_called_once_with("token-for-nonexistent-video")

# --- Correção Erro 4 ---
def test_secure_download_video_not_completed(client, test_user, db_session):
    # Usa 'with patch' com o alvo correto
    with patch("app.api.videos.verify_download_token", return_value=(2, test_user.id)) as mock_verify:
        # Cria vídeo PENDING com ID 2
        video = Video(
            id=2,
            filename="pending.mp4",
            storage_input="uploads/pending.mp4",
            status=VideoStatus.PENDING,
            user_id=test_user.id
        )
        db_session.add(video)
        db_session.commit()

        response = client.get("/videos/secure-download/token-for-pending-video")
        # O endpoint deve retornar 404 se o vídeo não estiver COMPLETED
        assert response.status_code == 404
        assert "Video not available" in response.json()["detail"]
        # Verifica se o mock foi chamado
        mock_verify.assert_called_once_with("token-for-pending-video")