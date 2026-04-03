from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ---------------------------
# REGISTER
# ---------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "reception")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if role not in ["doctor", "reception"]:
        return jsonify({"error": "Role must be 'doctor' or 'reception'"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


# ---------------------------
# SETUP (create test users)
# ---------------------------
@auth_bp.route("/setup", methods=["GET"])
def setup():
    if User.query.filter_by(username="doctor1").first():
        return jsonify({"message": "Users already exist"}), 200

    db.session.add(User(username="doctor1", password=generate_password_hash("doctor123"), role="doctor"))
    db.session.add(User(username="reception1", password=generate_password_hash("reception123"), role="reception"))
    db.session.commit()
    return jsonify({"message": "Users created successfully!"}), 201


# ---------------------------
# LOGIN
# ---------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # ✅ identity must be a string
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }), 200