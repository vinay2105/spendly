from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm_password", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for msg in errors:
                flash(msg, "error")
            return render_template("register.html")

        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                flash("Email already registered.", "error")
                return render_template("register.html")

            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()
        finally:
            conn.close()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html")

        conn = get_db()
        try:
            row = conn.execute(
                "SELECT id, name, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        finally:
            conn.close()

        if row is None or not check_password_hash(row["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"]   = row["id"]
        session["user_name"] = row["name"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You've been signed out.", "success")
    return redirect(url_for("landing"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        elif "@" not in email:
            errors.append("Please enter a valid email address.")

        if not errors:
            conn = get_db()
            try:
                taken = conn.execute(
                    "SELECT id FROM users WHERE email = ? AND id != ?",
                    (email, session["user_id"]),
                ).fetchone()
                if taken:
                    errors.append("That email is already in use by another account.")
                else:
                    conn.execute(
                        "UPDATE users SET name = ?, email = ? WHERE id = ?",
                        (name, email, session["user_id"]),
                    )
                    conn.commit()
                    session["user_name"] = name
                    flash("Profile updated successfully.", "success")
                    return redirect(url_for("profile"))
            finally:
                conn.close()

        for msg in errors:
            flash(msg, "error")
        return redirect(url_for("profile"))

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
    finally:
        conn.close()

    member_since = datetime.strptime(user["created_at"][:10], "%Y-%m-%d").strftime("%B %d, %Y")
    return render_template("profile.html", user=user, member_since=member_since)


@app.route("/profile/edit")
def profile_edit():
    return redirect(url_for("profile"))


@app.route("/profile/password", methods=["POST"])
def profile_password():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    current = request.form.get("current_password", "").strip()
    new     = request.form.get("new_password", "").strip()
    confirm = request.form.get("confirm_password", "").strip()

    errors = []
    if not current:
        errors.append("Current password is required.")
    if not new:
        errors.append("New password is required.")
    elif len(new) < 8:
        errors.append("New password must be at least 8 characters.")
    if not confirm:
        errors.append("Please confirm your new password.")
    elif new and new != confirm:
        errors.append("Passwords do not match.")

    if errors:
        for msg in errors:
            flash(msg, "error")
        return redirect(url_for("profile"))

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
        if not check_password_hash(row["password_hash"], current):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("profile"))
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new), session["user_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    flash("Password updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
