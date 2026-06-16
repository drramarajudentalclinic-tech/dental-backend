from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request

import os

from config import Config
from database import db

# ---------------------------
# Import Blueprints
# ---------------------------
from routes.patients       import patients_bp
from routes.visits         import visits_bp
from routes.medical        import medical_bp
from routes.allergies      import allergy_bp
from routes.habits         import habits_bp
from routes.dental_chart   import dental_bp
from routes.findings       import findings_bp
from routes.images         import images_bp, run_image_migrations
from routes.consultation   import consult_bp
from routes.prescription   import presc_bp
from routes.women          import women_bp
from routes.doctor         import doctor_bp
from routes.payments       import payments_bp, run_payment_migrations, run_visit_migrations
from routes.receipts       import receipts_bp
from routes.family_doctor  import family_doctor_bp
from routes.consent        import consent_bp
from routes.appointments   import appointments_bp
from routes.other_expenses import other_expenses_bp, run_other_expense_migrations
from routes.auth           import auth_bp
from routes.cbct           import cbct_bp, run_cbct_migrations

# ---------------------------
# Single source of truth for allowed origins
# ---------------------------
ALLOWED_ORIGINS = [
    "https://dental-frontend-zp4w.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
]

# ---------------------------
# CREATE APP
# ---------------------------
app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB — must be after Flask()

# ---------------------------
# JWT CONFIGURATION
# ---------------------------
app.config["JWT_SECRET_KEY"]        = os.getenv("JWT_SECRET_KEY", "fallback-secret")
app.config["JWT_TOKEN_LOCATION"]    = ["headers", "query_string"]
app.config["JWT_QUERY_STRING_NAME"] = "token"

jwt = JWTManager(app)

# ---------------------------
# CORS CONFIGURATION
# ---------------------------
CORS(
    app,
    resources={r"/api/*": {
        "origins":        ALLOWED_ORIGINS,
        "methods":        ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers":  ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age":        600,
    }},
    supports_credentials=True,
)


# ---------------------------
# JWT PROTECTION
# ---------------------------
@app.before_request

def protect_all_routes():
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        res = make_response()
        if origin in ALLOWED_ORIGINS:
            res.headers["Access-Control-Allow-Origin"]      = origin
            res.headers["Access-Control-Allow-Credentials"] = "true"
            res.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            res.headers["Access-Control-Allow-Headers"]     = "Content-Type, Authorization"
            res.headers["Access-Control-Max-Age"]           = "600"
        return res, 200

    public_paths = [
        "/",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/setup",
    
        "/health",
    ]

    if request.path in public_paths:
        return

    if request.path.startswith("/api/receipts/") and (
        request.path.endswith("/preview") or request.path.endswith("/download")
    ):
        return

    try:
        verify_jwt_in_request()
    except Exception as e:
        return jsonify({"error": "Unauthorized", "message": str(e)}), 401

# ---------------------------
# AFTER REQUEST — Ensure CORS headers on every response
# ---------------------------
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"]      = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"]     = "Content-Type, Authorization"
    return response


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
    run_cbct_migrations(app)

    # Migrate allergy_records to new row-based schema
    try:
        with db.engine.connect() as conn:
            for col, col_type in [
    ("type",               "VARCHAR(100)"),
    ("allergen",           "VARCHAR(200)"),
    ("reaction",           "TEXT"),
    ("severity",           "VARCHAR(50)"),
    ("notes",              "TEXT"),
    ("no_known_allergies",   "BOOLEAN DEFAULT FALSE"),
]:
                try:
                    conn.execute(db.text(f'ALTER TABLE allergy_records ADD COLUMN {col} {col_type}'))
                    conn.commit()
                    print(f"allergy_records.{col} added")
                except Exception:
                    pass
            for old_col in ["drug_allergy", "food_allergy", "latex_allergy",
                            "iodine_allergy", "anesthesia_allergy", "other_allergy",
                            ]:
                try:
                    conn.execute(db.text(f'ALTER TABLE allergy_records DROP COLUMN {old_col}'))
                    conn.commit()
                    print(f"allergy_records.{old_col} dropped")
                except Exception:
                    pass
            try:
                conn.execute(db.text(
                    'ALTER TABLE allergy_records DROP CONSTRAINT IF EXISTS allergy_records_patient_id_key'
                ))
                conn.commit()
                print("allergy_records unique constraint dropped")
            except Exception:
                pass
    except Exception as e:
        print(f"Allergy migration skipped: {e}")

    print("DONE ✅")


# ---------------------------
# REGISTER BLUEPRINTS
# ---------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(patients_bp)

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
    cbct_bp,
    other_expenses_bp,
]

for bp in other_blueprints:
    app.register_blueprint(bp, url_prefix="/api")


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