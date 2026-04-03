from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from database import db

# ✅ IMPORT your existing model here (VERY IMPORTANT)
# Change this path based on your project
# Example options:
# from models import User
# from models.user import User
# from routes.doctor import Doctor as User

from models import User   # 🔁 UPDATE THIS IF NEEDED

# ✅ DEFINE BLUEPRINT
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
    role = data.get("role", "reception")  # ✅ get role, default to reception

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # ✅ Validate role
    if role not in ["doctor", "reception"]:
        return jsonify({"error": "Role must be 'doctor' or 'reception'"}), 400

    # Check existing user
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    # Hash password
    hashed_password = generate_password_hash(password)

    # Create user with role
    new_user = User(username=username, password=hashed_password, role=role)  # ✅ save role
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route("/setup", methods=["GET"])
def setup():
    from werkzeug.security import generate_password_hash
    
    # Check if already created
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

    # Find user
    user = User.query.filter_by(username=username).first()

    # Validate password
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Create JWT token
    access_token = create_access_token(identity=user.id)

    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "username": user.username,
        "role": user.role  # ✅ return role so frontend can redirect correctly
    }), 200
    