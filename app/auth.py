from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db

auth = Blueprint("auth", __name__)


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def current_username():
    return session.get("username")


@auth.get("/login")
def login():
    if "user_id" in session:
        return redirect(url_for("main.home"))
    return render_template("login.html")


@auth.post("/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Please enter a username and password.", "error")
        return render_template("login.html"), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password.", "error")
        return render_template("login.html"), 401

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return redirect(url_for("main.home"))


@auth.get("/register")
def register():
    if "user_id" in session:
        return redirect(url_for("main.home"))
    return render_template("register.html")


@auth.post("/register")
def register_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm  = request.form.get("confirm", "")

    if not username or not password:
        flash("Username and password are required.", "error")
        return render_template("register.html"), 400

    if password != confirm:
        flash("Passwords do not match.", "error")
        return render_template("register.html"), 400

    if len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return render_template("register.html"), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        flash("That username is already taken.", "error")
        return render_template("register.html"), 409

    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password, method="pbkdf2:sha256")),
    )
    db.commit()

    flash("Account created! You can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
