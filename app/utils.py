"""
app/utils.py — Shared helper utilities.

Contains the login_required decorator that protects routes
from being accessed by unauthenticated users.
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """
    Route decorator that requires the user to be logged in.

    If the user has no active session (i.e. session["user_id"] is missing),
    they are redirected to the login page with a warning message.

    Usage — place @login_required AFTER @app.route / @blueprint.route:

        @tasks_bp.route("/dashboard")
        @login_required
        def dashboard():
            ...

    The @wraps(f) call preserves the original function name and docstring,
    which is important for Flask's internal URL routing.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
