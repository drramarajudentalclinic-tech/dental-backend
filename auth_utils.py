"""
Shared role-based access control (RBAC) helpers.

WHY THIS EXISTS
────────────────
Both doctor.py and patients.py let Doctor and Reception hit almost the same
URLs (search, complete-history, etc.) so both roles can pull up any
patient's record without needing an appointment first. That part is fine
and intentional.

The problem is the *write* routes: nothing was stopping a Reception login
from calling POST /doctor/visit/<id>/start (a clinical action) or a Doctor
login from calling PUT /api/patients/<id> to rewrite registration details.
The frontend hides those buttons per-role, but hiding a button doesn't
stop a direct API call — the check has to live on the server.

USAGE
────────────────
    from auth_utils import require_role

    @patients_bp.route("/<int:patient_id>", methods=["PUT"])
    @require_role("reception")
    def update_patient(patient_id):
        ...

ASSUMPTION (please verify against your login endpoint)
────────────────
This assumes the JWT issued at login carries the user's role, e.g.:

    create_access_token(identity=user.id, additional_claims={"role": "reception"})

If your app instead stores the role elsewhere (a DB lookup by user id,
a different claim name, etc.), update get_current_role() below — every
other route in the app can keep using require_role()/get_current_role()
unchanged.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def get_current_role():
    """Returns the caller's role (lowercased), or '' if none is set."""
    claims = get_jwt()
    return (claims.get("role") or "").strip().lower()


def require_role(*allowed_roles):
    """
    Restrict a route to the given role(s). "admin" is always allowed on
    top of whatever is listed, since admins can do anything Doctor or
    Reception can do.

    Returns 401 if there's no valid token, 403 if the token's role isn't
    in the allowed set.
    """
    allowed = {r.strip().lower() for r in allowed_roles} | {"admin"}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            role = get_current_role()
            if role not in allowed:
                return jsonify({
                    "error": "Forbidden",
                    "detail": (
                        f"This action requires one of: {', '.join(sorted(allowed))}. "
                        f"Your role: {role or 'unknown'}."
                    ),
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_login(fn):
    """
    Just requires *some* valid logged-in user (Doctor or Reception or
    admin) — no role restriction. Use this on the shared
    search/view/history endpoints both roles need without an appointment.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper