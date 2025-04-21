# app/workers/celery_worker.py
from celery import Celery
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.db.database import SessionLocal
from datetime import datetime
from app.services.video_processor import VideoProcessor
import os

celery = Celery(
    'video_processor',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery.task
def process_video(video_path: str, output_path: str, video_id: int):
    try:
        # Atualiza status para processando
        db = SessionLocal()
        video = db.query(Video).filter(Video.id == video_id).first()
        video.status = VideoStatus.PROCESSING
        db.commit()

        # Usa o serviço de processamento
        processor = VideoProcessor()
        processor.process_video(video_path, output_path)

        # Atualiza status para completo
        video.status = VideoStatus.COMPLETED
        video.processed_at = datetime.now()
        video.output_path = output_path
        db.commit()

        # Limpa o vídeo original
        os.remove(video_path)
        
        return {"status": "success", "output_path": output_path}

    except Exception as e:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = VideoStatus.FAILED
            db.commit()
        raise e

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
    task_time_limit=3600,  # limite de 1 hora por tarefa
    worker_prefetch_multiplier=1,  # processa uma tarefa por vez
    worker_max_tasks_per_child=100  # reinicia worker após 100 tarefas
)