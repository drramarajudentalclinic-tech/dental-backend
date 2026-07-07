import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    _db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://dental_db_user_main:tcRpSQcFsaph9pi7bFeHdtU0sBnLyrI3@dpg-d77qmi2dbo4c73av3jo0-a/dental_db_malm"
    )

    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    # Add SSL if missing
    if "sslmode=" not in _db_url:
        if "?" in _db_url:
            _db_url += "&sslmode=require"
        else:
            _db_url += "?sslmode=require"

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = "clinic-secret"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 20,
        "pool_size": 5,
        "max_overflow": 2,
        "connect_args": {
            "sslmode": "require"
        }
    }