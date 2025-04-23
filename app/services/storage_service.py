from google.cloud import storage
from datetime import timedelta
from app.core.config import settings

class StorageService:
    def __init__(self):
        # se GOOGLE_APPLICATION_CREDENTIALS estiver definido ou no Cloud Run,
        # o client assume as credenciais corretas
        self.client = storage.Client()
        self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)

    def upload_file(self, local_path: str, blob_name: str):
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        return blob_name

    def download_file(self, blob_name: str, local_path: str):
        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(local_path)

    def generate_signed_url(self, blob_name: str) -> str:
        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            expiration=timedelta(hours=settings.DOWNLOAD_URL_EXPIRE_HOURS)
        )
        return url