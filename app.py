from dotenv import load_dotenv
import models
load_dotenv()
import time
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
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
from routes.cbct_backend import cbct_bp, run_cbct_migrations
from routes.billing_ledger import billing_ledger_bp, run_billing_ledger_migrations, backfill_legacy_visit_charges

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

    # Patient search
    if request.path.startswith("/patients/search"):
        return

    if request.path.startswith("/api/patients/search"):
        return

    # Patient history
    # NOTE: /history was replaced by /complete-history (see patients.py) —
    # kept this exemption for any old bookmarked/cached callers, and added
    # the same exemption for the new route so behavior is unchanged.
    if request.path.startswith("/patients/") and request.path.endswith("/history"):
        return

    if request.path.startswith("/api/patients/") and request.path.endswith("/history"):
        return

    if request.path.startswith("/patients/") and request.path.endswith("/complete-history"):
        return

    if request.path.startswith("/api/patients/") and request.path.endswith("/complete-history"):
        return

    # Receipts
    if request.path.startswith("/api/receipts/") and (
        request.path.endswith("/preview")
        or request.path.endswith("/download")
    ):
        return

    try:
        verify_jwt_in_request()
    except Exception as e:
        return jsonify({
            "error": "Unauthorized",
            "message": str(e)
        }), 401
# ---------------------------
# AFTER REQUEST — Ensure CORS headers on every response
# ---------------------------
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# ---------------------------
# DB STARTUP HELPERS
# ---------------------------
def wait_for_db(app, max_retries=10, delay_seconds=3):
    """
    Block until the database accepts connections, or give up after
    max_retries. Prevents gunicorn worker boot from crashing on a
    cold-starting Postgres instance (common on Render after a restart
    or scale-from-zero).
    """
    with app.app_context():
        for attempt in range(1, max_retries + 1):
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("SELECT 1"))
                print(f"Database reachable after {attempt} attempt(s) ✅")
                return True
            except OperationalError as e:
                print(f"[wait_for_db] attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    print("[wait_for_db] giving up — DB never became reachable")
                    return False
                time.sleep(delay_seconds)


def safe_migrate(name, fn, *args, **kwargs):
    """
    Run a migration function without letting its failure crash the
    whole app import/boot. Logs success/failure either way.
    """
    try:
        fn(*args, **kwargs)
        print(f"✅ {name} migration completed")
    except Exception as e:
        print(f"⚠️ {name} migration failed (continuing): {e}")


# ---------------------------
# INIT DB
# ---------------------------
print("DATABASE_URL =", os.getenv("DATABASE_URL"))

db.init_app(app)

if not wait_for_db(app):
    # DB never became reachable after retries. We continue booting rather
    # than crashing the whole process — DB-dependent routes will error
    # until connectivity is restored, but the app (and /health) stays up
    # instead of gunicorn endlessly restarting.
    print("WARNING: starting without confirmed DB connectivity")

with app.app_context():
    print("Database connected ✅")

    # Create all tables
    db.create_all()

print("Running migrations...")

with app.app_context():
    safe_migrate("billing_ledger", run_billing_ledger_migrations)
    safe_migrate("backfill_legacy_visit_charges", backfill_legacy_visit_charges)
    safe_migrate("payments", run_payment_migrations, app)
    safe_migrate("visits", run_visit_migrations, app)
    safe_migrate("images", run_image_migrations, app)
    safe_migrate("cbct", run_cbct_migrations, app)
    safe_migrate("other_expenses", run_other_expense_migrations, app)

with app.app_context():

    # --------------------------------------------------
    # Allergy table migration
    # --------------------------------------------------
    try:
        with db.engine.connect() as conn:

            inspector = inspect(db.engine)

            existing_columns = [
                c["name"] for c in inspector.get_columns("allergy_records")
            ]

            columns = [
                ("allergy_type", "VARCHAR(50)"),
                ("allergen", "VARCHAR(255)"),
                ("reaction", "VARCHAR(255)"),
                ("severity", "VARCHAR(50)"),
                ("notes", "TEXT"),
                ("created_at", "TIMESTAMP"),
                ("updated_at", "TIMESTAMP"),
            ]

            for col, col_type in columns:
                if col not in existing_columns:
                    conn.execute(
                        db.text(
                            f"ALTER TABLE allergy_records ADD COLUMN {col} {col_type}"
                        )
                    )

            conn.commit()

        print("✅ Allergy migration completed")

    except Exception as e:
        print(f"Allergy migration skipped: {e}")
    # --------------------------------------------------
    # Habits table migration
    # --------------------------------------------------
    try:
        with db.engine.connect() as conn:

            inspector = inspect(db.engine)
            existing_columns = [
                c["name"] for c in inspector.get_columns("habits")
            ]

            columns = [
                ("smoking", "TEXT"),
                ("alcohol", "TEXT"),
                ("tobacco", "TEXT"),
                ("pan_chewing", "TEXT"),
                ("spicy_foods", "TEXT"),
                ("no_habits", "BOOLEAN DEFAULT FALSE"),
                ("updated_at", "TIMESTAMP"),
            ]

            for col, dtype in columns:
                if col not in existing_columns:
                    conn.execute(
                        db.text(
                            f"ALTER TABLE habits ADD COLUMN {col} {dtype}"
                        )
                    )

            conn.commit()
            print("✅ Habits migration completed")

    except Exception as e:
        print(f"Habits migration failed: {e}")

    # --------------------------------------------------
    # Prescriptions table migration
    # --------------------------------------------------
    try:
        with db.engine.connect() as conn:

            inspector = inspect(db.engine)
            existing_columns = [
                c["name"] for c in inspector.get_columns("prescriptions")
            ]

            columns = [
                ("patient_name",         "VARCHAR(150)"),
                ("patient_age",          "VARCHAR(20)"),
                ("patient_gender",       "VARCHAR(10)"),
                ("case_number",          "VARCHAR(50)"),
                ("date",                 "VARCHAR(20)"),
                ("diagnosis",            "TEXT"),
                ("advice",               "TEXT"),
                ("treatment_done_today", "TEXT"),
                ("medicines",            "TEXT"),
                ("follow_up_date",       "VARCHAR(30)"),
                ("follow_up_time",       "VARCHAR(20)"),
                ("status",               "VARCHAR(20) DEFAULT 'confirmed'"),
                ("drug_name",            "VARCHAR(150)"),
                ("dosage",               "VARCHAR(50)"),
                ("frequency",            "VARCHAR(50)"),
                ("duration",             "VARCHAR(50)"),
                ("instructions",         "TEXT"),
                ("doctor",               "VARCHAR(100)"),
                ("created_at",           "TIMESTAMP"),
            ]

            for col, col_type in columns:
                if col not in existing_columns:
                    conn.execute(
                        db.text(
                            f"ALTER TABLE prescriptions ADD COLUMN {col} {col_type}"
                        )
                    )
                    print(f"[prescriptions migration] Added {col} ✓")

            conn.commit()

        print("✅ Prescriptions migration completed")

    except Exception as e:
        print(f"Prescriptions migration failed: {e}")
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
    billing_ledger_bp,
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