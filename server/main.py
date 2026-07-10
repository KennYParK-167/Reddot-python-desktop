from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

# .ENV LAUNCH.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

APP_NAME = os.getenv("APP_NAME", "ProjetMessage")
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquant. Crée `server/.env` (voir `.env.example`) et renseigne une URL MySQL."
    )
    

# MYSQL.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user" 

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum("user", "admin"), nullable=False, server_default="user")
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    messages: Mapped[list["Message"]] = relationship(back_populates="user")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    user: Mapped[Optional[User]] = relationship(back_populates="messages")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# JWT: FAIT PAR IA.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Mot de passe trop long (bcrypt <= 72 octets).",
        )
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    pw_bytes = password.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))


def create_access_token(*, subject: str, role: str, user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
        "uid": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

class AuthUser(BaseModel):
    id: int
    username: str
    role: str


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AuthUser:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        uid: int = payload.get("uid")
        if not username or not role or not uid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide") from e

    user = db.scalar(select(User).where(User.id == uid))
    if not user or user.username != username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    return AuthUser(id=user.id, username=user.username, role=user.role)


def require_admin(current: AuthUser = Depends(get_current_user)) -> AuthUser:
    if current.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès admin requis")
    return current



# API SCHEMES.
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_length_bytes_ok(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mot de passe trop long (bcrypt <= 72 octets).")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class MessageCreate(BaseModel):
    message_text: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: int
    username: str
    message_text: str
    timestamp: datetime


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime