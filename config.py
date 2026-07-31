import os
from datetime import timedelta

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Local PostgreSQL fix
    if DATABASE_URL and "localhost" in DATABASE_URL:
        if "sslmode=" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=disable"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = "clinic-secret"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 20,
        "pool_size": 5,
        "max_overflow": 2
    }