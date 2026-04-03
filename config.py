import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "clinic.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "clinic-secret"

    # ✅ JWT token valid for 7 days (perfect for demo)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)