from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base
from passlib.hash import bcrypt

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    videos = relationship("Video", back_populates="users")

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hash(password)