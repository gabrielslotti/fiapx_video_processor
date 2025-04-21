from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_current_user
from app.models.video import Video, VideoStatus
from app.workers.celery_worker import process_video
from app.db.database import get_db
import os
import uuid
from app.core.config import settings

router = APIRouter()

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Garante que os diretórios existem
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    # Salva o arquivo
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
 
    # Cria registro do vídeo
    video = Video(
        filename=file.filename,
        status=VideoStatus.PENDING,
        user_id=current_user.id
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Inicia processamento assíncrono
    output_path = os.path.join(settings.OUTPUT_DIR, f"{video.id}.zip")
    process_video.delay(file_path, output_path, video.id)
    
    return {"message": "Video upload started", "video_id": video.id}

@router.get("/status")
async def get_videos_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    videos = db.query(Video).filter(Video.user_id == current_user.id).all()
    return [
        {
            "id": video.id,
            "filename": video.filename,
            "status": video.status.value,
            "created_at": video.created_at,
            "processed_at": video.processed_at
        }
        for video in videos
    ]

@router.get("/download/{video_id}")
async def download_video(
    video_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Video not processed yet")
    
    return FileResponse(
        video.output_path,
        filename=f"{video.filename}_frames.zip",
        media_type="application/zip"
    )