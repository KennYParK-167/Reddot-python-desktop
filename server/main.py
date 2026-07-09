from __future__ import annotations

import os

from dotenv import load_dotenv


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


