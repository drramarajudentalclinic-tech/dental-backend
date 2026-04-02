from flask import Flask, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager

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
from routes.auth import auth_bp
# ---------------------------
# CREATE APP
# ---------------------------
app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------
import os  # ✅ ADD THIS

# ---------------------------
# JWT CONFIGURATION
# ---------------------------
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "fallback-secret")
jwt = JWTManager(app)

# ---------------------------
# ENABLE CORS
# ---------------------------
CORS(
    app,
    resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 600,
    }},
    supports_credentials=True,
)

# ---------------------------
# GLOBAL OPTIONS HANDLER
# ---------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        res = make_response()
        if origin in allowed_origins:
            res.headers["Access-Control-Allow-Origin"]      = origin
            res.headers["Access-Control-Allow-Credentials"] = "true"
            res.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            res.headers["Access-Control-Allow-Headers"]     = "Content-Type, Authorization, X-Requested-With"
            res.headers["Access-Control-Max-Age"]           = "600"
        return res, 200

# ---------------------------
# INIT DB
# ---------------------------

db.init_app(app)

with app.app_context():
    print("Creating tables...")
    db.create_all()

    print("Running payment migrations...")
    run_payment_migrations(app)

    print("Running image migrations...")
    run_image_migrations(app)

    print("Running visit migrations...")
    run_visit_migrations(app)

    print("Running other expense migrations...")
    run_other_expense_migrations(app)

    print("DONE ✅")
# ---------------------------
# REGISTER BLUEPRINTS
# ---------------------------
app.register_blueprint(patients_bp)
app.register_blueprint(auth_bp)   # ✅ correct place

blueprints = [
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

for bp in blueprints:
    app.register_blueprint(bp, url_prefix="/api")

# already has /api prefix internally
app.register_blueprint(other_expenses_bp)

# ---------------------------
# DEFAULT ROUTE
# ---------------------------
@app.route("/")
def index():
    return {"status": "Server running"}, 200

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

