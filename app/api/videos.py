import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
from app.core.security import get_current_user, verify_download_token 
from app.db.database import get_db
from app.models.video import Video, VideoStatus
# from app.services.storage_service import StorageService
from app.workers.celery_worker import process_video

router = APIRouter()
# storage = StorageService()

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db)
):
    from app.services.storage_service import StorageService
    storage = StorageService()

    # define um nome único no bucket
    unique_id = str(uuid.uuid4())
    blob_in = f"uploads/{unique_id}_{file.filename}"

    # salva localmente temporário
    tmp_file = f"/tmp/{unique_id}"
    with open(tmp_file, "wb") as f:
        f.write(await file.read())

    # envia ao bucket
    storage.upload_file(tmp_file, blob_in)
    os.remove(tmp_file)

    # cria registro no banco
    video = Video(
        filename=file.filename,
        storage_input=blob_in,
        status=VideoStatus.PENDING,
        user_id=current_user.id
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # enfileira a task
    blob_out = f"outputs/{video.id}.zip"
    process_video.delay(blob_in, blob_out, video.id)

    return {"message": "Video upload started", "video_id": video.id}

@router.get("/status")
async def get_videos_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.storage_service import StorageService
    storage = StorageService()

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

@router.get("/secure-download/{token}")
async def secure_download_video(token: str, db: Session=Depends(get_db)):
    from app.services.storage_service import StorageService
    storage = StorageService()

    res = verify_download_token(token)
    if not res:
        raise HTTPException(403, "Invalid or expired link")

    video_id, user_id = res
    vid = db.query(Video).filter(Video.id==video_id, Video.user_id==user_id).first()
    if not vid or vid.status!=VideoStatus.COMPLETED:
        raise HTTPException(404, "Video not available")
    
    # gera um signed URL GCS e faz redirect
    signed = storage.generate_signed_url(vid.storage_output)
    return RedirectResponse(signed)