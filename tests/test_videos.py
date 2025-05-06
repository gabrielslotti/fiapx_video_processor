import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
import io
from app.models.video import Video, VideoStatus

@pytest.fixture
def mock_celery_task():
    with patch("app.api.videos.process_video.delay") as mock_delay:
        yield mock_delay

def test_upload_video(authorized_client, mock_celery_task, test_user, db_session, mock_gcs_client):
    file_content = b"dummy video file content"
    response = authorized_client.post(
        "/videos/upload",
        files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert data["message"] == "Video upload started"

    mock_gcs_client.bucket.return_value.blob.return_value.upload_from_filename.assert_called_once()

    mock_celery_task.assert_called_once()
    args, kwargs = mock_celery_task.call_args
    assert len(args) == 3
    assert args[2] == data["video_id"]

    video_in_db = db_session.query(Video).filter(Video.id == data["video_id"]).first()
    assert video_in_db is not None
    assert video_in_db.filename == "test.mp4"
    assert video_in_db.status == VideoStatus.PENDING
    assert video_in_db.user_id == test_user.id
    assert video_in_db.storage_input.startswith("uploads/")

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

def test_secure_download_invalid_token(client):
    with patch("app.api.videos.verify_download_token", return_value=None) as mock_verify:
         response = client.get("/videos/secure-download/invalid-token")
         assert response.status_code == 403
         assert "Invalid or expired" in response.json()["detail"]
         mock_verify.assert_called_once_with("invalid-token")


def test_secure_download_success(client, test_user, db_session, mock_gcs_client):
    with patch("app.api.videos.verify_download_token", return_value=(1, test_user.id)) as mock_verify:
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

        mock_verify.assert_called_once_with("valid-token-mocked")
        
        mock_gcs_client.bucket.return_value.blob.return_value.generate_signed_url.assert_called_once()

def test_secure_download_video_not_found(client, test_user):
    with patch("app.api.videos.verify_download_token", return_value=(999, test_user.id)) as mock_verify:
        response = client.get("/videos/secure-download/token-for-nonexistent-video")
        assert response.status_code == 404
        assert "Video not available" in response.json()["detail"]
        mock_verify.assert_called_once_with("token-for-nonexistent-video")

def test_secure_download_video_not_completed(client, test_user, db_session):
    with patch("app.api.videos.verify_download_token", return_value=(2, test_user.id)) as mock_verify:
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
        assert response.status_code == 404
        assert "Video not available" in response.json()["detail"]
        mock_verify.assert_called_once_with("token-for-pending-video")