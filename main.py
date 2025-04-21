from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, videos, users
from app.core.config import settings

app = FastAPI(title="FIAP X - Video Processing Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(users.router, prefix="/users", tags=["users"])