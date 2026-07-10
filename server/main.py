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
    
    
# FAST API INIT.
app = FastAPI(title=APP_NAME)


@app.on_event("startup")
def startup() -> None:

    auto_create = os.getenv("AUTO_CREATE_TABLES", "true").strip().lower() in ("1", "true", "yes", "y", "on")
    if not auto_create:
        return

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[startup] WARNING: impossible de créer les tables automatiquement: {e}")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "app": APP_NAME}


# INSCRIPTION. [FAST API POST]
@app.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=409, detail="Nom d'utilisateur déjà utilisé")

    user = User(username=payload.username, password_hash=hash_password(payload.password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "username": user.username, "role": user.role}




# CONNEXION. [FAST API GET]
@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_access_token(subject=user.username, role=user.role, user_id=user.id)
    return TokenResponse(access_token=token, username=user.username, role=user.role)




# CHAT. [FAST API GET]
@app.get("/messages", response_model=list[MessageOut])
def get_messages(
    since_id: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    current: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    # Retourne les messages dont l'id est supérieur à since_id (pratique pour le polling)
    stmt = select(Message).where(Message.id > since_id).order_by(Message.id.asc()).limit(limit)
    rows = db.scalars(stmt).all()
    return [
        MessageOut(id=m.id, username=m.username, message_text=m.message_text, timestamp=m.timestamp)
        for m in rows
    ]


@app.post("/messages", status_code=201)
def post_message(
    payload: MessageCreate,
    current: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    msg = Message(user_id=current.id, username=current.username, message_text=payload.message_text)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"id": msg.id, "timestamp": msg.timestamp}


# ...
@app.get("/admin/users", response_model=list[UserOut])
def admin_list_users(
    _admin: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    return [
        UserOut(id=u.id, username=u.username, role=u.role, created_at=u.created_at) for u in users
    ]


@app.delete("/admin/users/{user_id}", status_code=204)
def admin_delete_user(
    user_id: int,
    admin: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer son propre compte admin")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    db.delete(user)
    db.commit()


@app.get("/admin/messages", response_model=list[MessageOut])
def admin_list_messages(
    limit: int = Query(200, ge=1, le=1000),
    _admin: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    msgs = db.scalars(select(Message).order_by(Message.id.desc()).limit(limit)).all()
    msgs.reverse()
    return [
        MessageOut(id=m.id, username=m.username, message_text=m.message_text, timestamp=m.timestamp)
        for m in msgs
    ]


@app.delete("/admin/messages/{message_id}", status_code=204)
def admin_delete_message(
    message_id: int,
    _admin: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    msg = db.scalar(select(Message).where(Message.id == message_id))
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")
    db.delete(msg)
    db.commit()

