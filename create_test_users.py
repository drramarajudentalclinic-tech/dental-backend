from app import app
from database import db
from models import User

users = [
    {
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    },
    {
        "username": "doctor1",
        "password": "doctor123",
        "role": "doctor"
    },
    {
        "username": "reception1",
        "password": "reception123",
        "role": "reception"
    }
]

with app.app_context():

    for u in users:

        existing = User.query.filter_by(username=u["username"]).first()

        if existing:
            print(f"⚠ {u['username']} already exists")
            continue

        user = User(
            username=u["username"],
            role=u["role"]
        )

        user.set_password(u["password"])

        db.session.add(user)

    db.session.commit()

    print("✅ Test users created successfully!")