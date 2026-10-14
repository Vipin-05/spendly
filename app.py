import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import (
    init_db,
    seed_db,
    get_user_by_email,
    create_user,
    get_user_by_id,
    update_user_name,
    get_user_expense_stats,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-spendly")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="All fields are required.",
                name=name,
                email=email,
            )

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return render_template(
                "register.html",
                error="Please enter a valid email address.",
                name=name,
                email=email,
            )

        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must be at least 8 characters long.",
                name=name,
                email=email,
            )

        existing_user = get_user_by_email(email)
        if existing_user:
            return render_template(
                "register.html",
                error="An account with this email already exists.",
                name=name,
                email=email,
            )

        password_hash = generate_password_hash(password)
        create_user(name, email, password_hash)
        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password.strip():
            return render_template(
                "login.html",
                error="All fields are required.",
                email=email,
            )

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password.",
                email=email,
            )

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("landing"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please sign in to access your profile.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("User account not found. Please sign in again.", "error")
        return redirect(url_for("login"))

    stats = get_user_expense_stats(user_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template(
                "profile.html",
                user=user,
                stats=stats,
                error="Full name cannot be empty.",
            )

        update_user_name(user_id, name)
        session["user_name"] = name
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user, stats=stats)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
