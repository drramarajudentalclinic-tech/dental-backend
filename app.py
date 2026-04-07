from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request

import os

from config import Config
from database import db

# ---------------------------
# Import Blueprints
# ---------------------------
from routes.patients      import patients_bp
from routes.visits        import visits_bp
from routes.medical       import medical_bp
from routes.allergies     import allergy_bp
from routes.habits        import habits_bp
from routes.dental_chart  import dental_bp
from routes.findings      import findings_bp
from routes.images        import images_bp, run_image_migrations
from routes.consultation  import consult_bp
from routes.prescription  import presc_bp
from routes.women         import women_bp
from routes.doctor        import doctor_bp
from routes.payments      import payments_bp, run_payment_migrations, run_visit_migrations
from routes.receipts      import receipts_bp
from routes.family_doctor import family_doctor_bp
from routes.consent       import consent_bp
from routes.appointments  import appointments_bp
from routes.other_expenses import other_expenses_bp, run_other_expense_migrations
from routes.auth          import auth_bp

# ---------------------------
# CREATE APP
# ---------------------------
app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------
# JWT CONFIGURATION
# ---------------------------
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "fallback-secret")
jwt = JWTManager(app)

# ---------------------------
# ✅ CORS CONFIGURATION
# ---------------------------
CORS(
    app,
    resources={r"/api/*": {
        "origins": [
            "https://dental-frontend-zp4w.onrender.com",
            "http://localhost:5173",
            "http://localhost:3000"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"],
    }},
    supports_credentials=True
)

# ---------------------------
# ✅ JWT PROTECTION
# ---------------------------
@app.before_request
def protect_all_routes():
    # ✅ Let Flask-CORS handle OPTIONS preflight — do NOT return a response here
    if request.method == "OPTIONS":
        return

    public_paths = [
        "/",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/setup",
        "/health",
    ]

    if request.path in public_paths:
        return

    # Allow receipt preview/download without JWT
    if request.path.startswith("/api/receipts/") and (
        request.path.endswith("/preview") or request.path.endswith("/download")
    ):
        return

    try:
        verify_jwt_in_request()
    except Exception as e:
        return jsonify({"error": "Unauthorized", "message": str(e)}), 401

# ---------------------------
# INIT DB
# ---------------------------
db.init_app(app)

with app.app_context():
    print("Creating tables...")
    db.create_all()

    try:
        with db.engine.connect() as conn:
            conn.execute(db.text(
                'ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT \'reception\''
            ))
            conn.commit()
            print("Role column added ✅")
    except Exception as e:
        print(f"Role column already exists or skipped: {e}")

    print("Running migrations...")
    run_payment_migrations(app)
    run_image_migrations(app)
    run_visit_migrations(app)
    run_other_expense_migrations(app)

    print("DONE ✅")

# ---------------------------
# REGISTER BLUEPRINTS
# ---------------------------

# ✅ Auth under /api
app.register_blueprint(auth_bp, url_prefix="/api")

# Patients (no prefix inside)
app.register_blueprint(patients_bp)

# Other APIs
other_blueprints = [
    visits_bp,
    medical_bp,
    allergy_bp,
    habits_bp,
    dental_bp,
    findings_bp,
    images_bp,
    consult_bp,
    presc_bp,
    women_bp,
    doctor_bp,
    payments_bp,
    receipts_bp,
    family_doctor_bp,
    consent_bp,
    appointments_bp,
]

for bp in other_blueprints:
    app.register_blueprint(bp, url_prefix="/api")

# Already has prefix
app.register_blueprint(other_expenses_bp)

# ---------------------------
# DEFAULT ROUTE
# ---------------------------
@app.route("/")
def index():
    return {"status": "Server running"}, 200

# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.route("/health")
def health():
    return {"status": "ok"}, 200

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)