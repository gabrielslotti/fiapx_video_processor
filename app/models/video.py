from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base
from app.models.user import User


class VideoStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    storage_input = Column(String, nullable=False)
    storage_output = Column(String, nullable=True)
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    users = relationship(User, back_populates="videos")