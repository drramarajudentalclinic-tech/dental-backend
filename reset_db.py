from app import app
from database import db

with app.app_context():
    db.session.execute(db.text("""
        TRUNCATE TABLE
        receipts,
        payments,
        cbct_annotations,
        cbct_volumes,
        cbct_files,
        images,
        prescriptions,
        consultations,
        other_findings,
        dental_chart,
        visits,
        woman_history,
        habits,
        allergy_records,
        medical_history,
        family_doctors,
        consents,
        patients
        RESTART IDENTITY CASCADE;
    """))

    db.session.commit()

print("Database reset successfully")