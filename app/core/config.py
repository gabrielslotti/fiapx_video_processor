# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Processing Service"
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "video_service"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"

    # Auth settings
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Files directories
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"

    # Celery
    TASK_TIME_LIMIT: int = 3600
    WORKER_PREFETCH_MULTIPLIER: int = 1
    WORKER_MAX_TASKS_PER_CHILD: int = 100
    
    # Email settings
    # SMTP Gmail
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "myemail@gmail.com"  # ex: seu-email@gmail.com
    SMTP_PASSWORD: str  = "app-token"# senha de app gerada no Google
    SMTP_SENDER: str = "Video Processor <seu-email@gmail.com>"
    BASE_URL: str = "http://localhost:8000"

    # GCS
    GCS_BUCKET_NAME: str = "my-gcs-bucket"
    # Credenciais, no GCP o próprio ambiente do Cloud Run ou Worker
    # já herda a Service Account correta, então não precisa setar arquivo.
    # Se for local, você pode apontar:
    # GOOGLE_APPLICATION_CREDENTIALS: str

    # Tempo de expiração do signed URL
    DOWNLOAD_URL_EXPIRE_HOURS: int = 24

    class Config:
        env_file = ".env"
        
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

# Sobrescrever DATABASE_URL se não estiver definido
if not settings.DATABASE_URL:
    settings.DATABASE_URL = settings.get_database_url()

# Garante que os diretórios necessários existem
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)