import pytest
import os
import shutil
from unittest.mock import patch

def test_upload_video(authorized_client, test_video, monkeypatch):
    # Mock para a task Celery
    with patch('app.api.videos.process_video.delay') as mock_task:
        # Abrir arquivo de vídeo
        with open(test_video, "rb") as f:
            response = authorized_client.post(
                "/videos/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")}
            )
        
        # Verificar resposta
        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert data["message"] == "Video upload started"
        
        # Verificar se a task foi chamada
        mock_task.assert_called_once()

def test_get_videos_status(authorized_client, test_db):
    # Primeiro upload de vídeo
    with patch('app.api.videos.process_video.delay'):
        with open("tests/resources/test_video.mp4", "rb") as f:
            authorized_client.post(
                "/videos/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")}
            )
    
    # Verificar status
    response = authorized_client.get("/videos/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "status" in data[0]
    assert "filename" in data[0]

def test_download_video_not_found(authorized_client):
    response = authorized_client.get("/videos/download/9999")
    assert response.status_code == 404

def test_download_video_not_processed(authorized_client, test_db):
    # Upload vídeo
    with patch('app.api.videos.process_video.delay'):
        with open("tests/resources/test_video.mp4", "rb") as f:
            response = authorized_client.post(
                "/videos/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")}
            )
    
    video_id = response.json()["video_id"]
    
    # Tentar download antes de processar
    response = authorized_client.get(f"/videos/download/{video_id}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Video not processed yet"}