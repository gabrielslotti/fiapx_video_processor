from celery import Celery
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.models.user import User
from app.db.database import SessionLocal
from datetime import datetime
from app.services.video_processor import VideoProcessor
from app.services.email_service import EmailService
import os
import traceback

celery = Celery(
    'video_processor',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery.task
def process_video(video_path: str, output_path: str, video_id: int):
    db = SessionLocal()
    try:
        # Atualiza status para processando
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception(f"Vídeo com ID {video_id} não encontrado")
            
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
        
        # Obtém o usuário do vídeo
        user = db.query(User).filter(User.id == video.user_id).first()
        if user:
            # Gera URL para download
            base_url = settings.BASE_URL.rstrip('/')
            download_url = f"{base_url}/videos/download/{video_id}"
            
            # Envia email de notificação de sucesso
            EmailService.send_success_notification(
                user_email=user.email,
                video_name=video.filename,
                download_url=download_url
            )
        
        return {"status": "success", "output_path": output_path}

    except Exception as e:
        # Captura o stacktrace completo
        error_details = traceback.format_exc()
        print(f"Erro no processamento do vídeo {video_id}: {error_details}")
        
        # Atualiza status para falha
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = VideoStatus.FAILED
            db.commit()
            
            # Obtém o usuário do vídeo
            user = db.query(User).filter(User.id == video.user_id).first()
            if user:
                # Envia email de notificação de erro
                EmailService.send_error_notification(
                    user_email=user.email,
                    video_name=video.filename,
                    error_message=str(e)
                )
        
        # Relança a exceção para que o Celery registre o erro
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
    task_time_limit=settings.TASK_TIME_LIMIT,                        # limite de 1 hora por tarefa
    worker_prefetch_multiplier=settings.WORKER_PREFETCH_MULTIPLIER,  # processa uma tarefa por vez
    worker_max_tasks_per_child=settings.WORKER_MAX_TASKS_PER_CHILD   # reinicia worker após 100 tarefas
)