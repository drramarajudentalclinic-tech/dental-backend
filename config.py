import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # ✅ PostgreSQL on Render (persistent, never resets)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://dental_db_malm_user:rX6cFWOuYLlrbgq9lB0kmQbQWNmrBQKl@dpg-d77qmi2dbo4c73av3jo0-a/dental_db_malm"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "clinic-secret"

    # ✅ JWT token valid for 7 days
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)