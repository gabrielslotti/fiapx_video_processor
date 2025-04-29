from celery import Celery
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.models.user import User
from app.db.database import SessionLocal
from app.services.video_processor import VideoProcessor
# from app.services.storage_service import StorageService
from app.services.email_service import EmailService
from datetime import datetime
import os
import uuid
import traceback

celery = Celery('video_processor', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery.task
def process_video(input_blob: str, output_blob: str, video_id: int):
    from app.services.storage_service import StorageService

    storage = StorageService()
    db = SessionLocal()
    
    try:
        video = db.query(Video).get(video_id)
        video.status = VideoStatus.PROCESSING
        db.commit()

        # Create local paths
        local_in = f"/tmp/{uuid.uuid4()}_{os.path.basename(input_blob)}"
        local_out = f"/tmp/{uuid.uuid4()}.zip"

        # Download video
        storage.download_file(input_blob, local_in)

        # Process
        VideoProcessor.process_video(local_in, local_out)

        # Upload ZIP
        storage.upload_file(local_out, output_blob)

        # Update database
        video.status = VideoStatus.COMPLETED
        video.processed_at = datetime.utcnow()
        video.storage_output = output_blob
        db.commit()

        # Remove local files
        os.remove(local_in)
        os.remove(local_out)

        # Notify user
        user = db.query(User).get(video.user_id)
        signed_url = storage.generate_signed_url(output_blob)
        EmailService.send_success_notification(user.email, video.filename, signed_url)

    except Exception as e:
        db.rollback()
        video = db.query(Video).get(video_id)
        video.status = VideoStatus.FAILED
        db.commit()
        user = db.query(User).get(video.user_id)
        EmailService.send_error_notification(user.email, video.filename, str(e))
        traceback.print_exc()
    finally:
        db.close()

# Configurações do Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.TASK_TIME_LIMIT,                        # limite de 1 hora por tarefa
    worker_prefetch_multiplier=settings.WORKER_PREFETCH_MULTIPLIER,  # processa uma tarefa por vez
    worker_max_tasks_per_child=settings.WORKER_MAX_TASKS_PER_CHILD   # reinicia worker após 100 tarefas
)