import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # ✅ PostgreSQL on Render — correct user is dental_db_user_main
    _db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://dental_db_user_main:tcRpSQcFsaph9pi7bFeHdtU0sBnLyrI3@dpg-d77qmi2dbo4c73av3jo0-a/dental_db_malm"
    )

    # Render sometimes gives postgres:// — SQLAlchemy needs postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI        = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY                     = "clinic-secret"

    # ✅ JWT token valid for 7 days
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)