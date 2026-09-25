"""
app/auth.py — Authentication blueprint.

Handles user registration, login, and logout.

Blueprint prefix: no URL prefix (routes are /register, /login, /logout).
"""

import re
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import create_user, get_user_by_email

# Create the blueprint — 'auth' is the name used in url_for('auth.login') etc.
auth_bp = Blueprint("auth", __name__)


# ----------------------------------------------------------------
# Helper
# ----------------------------------------------------------------

def is_valid_email(email):
    """
    Basic email format check using a regular expression.

    Accepts addresses like user@example.com, user.name+tag@domain.co.uk.
    This is intentionally simple — a confirmation email would be needed
    for full validation in a production application.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


# ----------------------------------------------------------------
# Registration
# ----------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    GET  /register — show the registration form.
    POST /register — validate input, create user, redirect to login.
    """
    # If the user is already logged in, send them to the home page.
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        # Pull form values and strip whitespace.
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # --- Server-side validation ---
        errors = []

        if not name:
            errors.append("Name is required.")
        elif len(name) > 100:
            errors.append("Name must be 100 characters or fewer.")

        if not email:
            errors.append("Email address is required.")
        elif not is_valid_email(email):
            errors.append("Please enter a valid email address.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match.")

        # Flash all validation errors and re-render the form.
        # We pass name/email back so the user doesn't have to retype them.
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html", name=name, email=email)

        # --- Check for duplicate email ---
        if get_user_by_email(email):
            flash(
                "An account with that email already exists. "
                "Please log in or use a different email.",
                "warning",
            )
            return render_template("auth/register.html", name=name, email=email)

        # --- Hash password and create user ---
        # generate_password_hash uses scrypt by default (secure and modern).
        # The plain-text password is never stored anywhere.
        password_hash = generate_password_hash(password)
        create_user(name, email, password_hash)

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    # GET request — show empty form
    return render_template("auth/register.html")


# ----------------------------------------------------------------
# Login
# ----------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  /login — show the login form.
    POST /login — verify credentials, set session, redirect to dashboard.
    """
    # If the user is already logged in, send them home.
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Basic presence check
        if not email or not password:
            flash("Please enter both your email address and password.", "danger")
            return render_template("auth/login.html", email=email)

        # Look the user up by email
        user = get_user_by_email(email)

        # check_password_hash compares the plain-text password against the
        # stored hash WITHOUT ever reversing the hash — this is one-way.
        if not user or not check_password_hash(user["password_hash"], password):
            # Use a generic message — don't confirm whether the email exists.
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login.html", email=email)

        # --- Successful login ---
        # session.clear() removes any stale data before writing new values.
        session.clear()
        session["user_id"]   = user["id"]
        session["user_name"] = user["name"]

        flash(f"Welcome back, {user['name']}!", "success")

        return redirect(url_for("tasks.dashboard"))

    # GET request — show empty form
    return render_template("auth/login.html")


# ----------------------------------------------------------------
# Logout
# ----------------------------------------------------------------

@auth_bp.route("/logout")
def logout():
    """
    GET /logout — clear the session and redirect to the home page.

    No POST needed here. For extra security in a production app you
    would use a POST with a CSRF token, but a GET is acceptable for
    this beginner project.
    """
    session.clear()
    flash("You have been logged out. See you next time!", "info")
    return redirect(url_for("index"))
