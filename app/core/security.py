# app/core/security.py
from datetime import datetime, timedelta
import hashlib
import hmac
from urllib.parse import quote_plus
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:      
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        # Converta o user_id para int, pois provavelmente foi salvo como string
        user_id_int = int(user_id)
    except JWTError as e:
        print(f"Erro ao decodificar JWT: {e}")
        raise credentials_exception
    except ValueError:
        print("Erro ao converter user_id para int")
        raise credentials_exception

    # Busca o usuário no banco de dados
    user = db.query(User).filter(User.id == user_id_int).first()
    
    print(f"Usuário encontrado: {user}")
    
    if user is None:
        raise credentials_exception
    return user

def generate_download_token(video_id: int, user_id: int, expiry_hours: int = 24):
    """
    Gera um token assinado para download de vídeo com validade limitada
    """
    # Timestamp de expiração
    expiry = int((datetime.now() + timedelta(hours=expiry_hours)).timestamp())
    
    # Dados a serem assinados
    data = f"{video_id}:{user_id}:{expiry}"
    
    # Assinatura usando HMAC
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Token completo: dados + assinatura
    token = f"{data}:{signature}"
    
    # Codifica para URL
    return quote_plus(token)

def verify_download_token(token: str):
    """
    Verifica se um token de download é válido
    Retorna (video_id, user_id) se válido, None caso contrário
    """
    try:
        # Decodifica o token
        parts = token.split(":")
        if len(parts) != 4:
            return None
        
        video_id, user_id, expiry, signature = parts
        
        # Verifica expiração
        if int(expiry) < datetime.now().timestamp():
            return None
        
        # Recria os dados originais
        data = f"{video_id}:{user_id}:{expiry}"
        
        # Verifica a assinatura
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        return int(video_id), int(user_id)
    except Exception:
        return None