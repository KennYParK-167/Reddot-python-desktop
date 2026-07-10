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