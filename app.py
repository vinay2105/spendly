from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"


CATEGORIES = ["Food", "Transport", "Bills", "Health",
              "Entertainment", "Shopping", "Other"]

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

    conn = get_db()
    try:
        expenses = conn.execute(
            "SELECT id, amount, category, date, description FROM expenses"
            " WHERE user_id = ? ORDER BY date DESC, created_at DESC",
            (session["user_id"],),
        ).fetchall()
    finally:
        conn.close()

    total_count  = len(expenses)
    total_amount = sum(e["amount"] for e in expenses)

    cat_totals = {}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
    biggest_cat = max(cat_totals, key=cat_totals.get) if cat_totals else "—"

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total_count=total_count,
        total_amount=total_amount,
        biggest_cat=biggest_cat,
    )


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


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        amount_raw   = request.form.get("amount", "").strip()
        category     = request.form.get("category", "").strip()
        date         = request.form.get("date", "").strip()
        description  = request.form.get("description", "").strip()

        errors = []
        amount_val = None
        try:
            amount_val = float(amount_raw)
            if amount_val <= 0:
                errors.append("Amount must be greater than zero.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid amount.")

        if category not in CATEGORIES:
            errors.append("Please select a valid category.")

        if not date:
            errors.append("Date is required.")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                errors.append("Please enter a valid date (YYYY-MM-DD).")

        if errors:
            for msg in errors:
                flash(msg, "error")
            return redirect(url_for("add_expense"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description)"
                " VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], amount_val, category, date, description or ""),
            )
            conn.commit()
        finally:
            conn.close()

        flash("Expense added.", "success")
        return redirect(url_for("dashboard"))

    today = datetime.today().strftime("%Y-%m-%d")
    return render_template("expenses/add.html", categories=CATEGORIES, today=today)


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = get_db()
    try:
        expense = conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (id,)
        ).fetchone()
    finally:
        conn.close()

    if expense is None or expense["user_id"] != session["user_id"]:
        flash("Expense not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        amount_raw  = request.form.get("amount", "").strip()
        category    = request.form.get("category", "").strip()
        date        = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        amount_val = None
        try:
            amount_val = float(amount_raw)
            if amount_val <= 0:
                errors.append("Amount must be greater than zero.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid amount.")

        if category not in CATEGORIES:
            errors.append("Please select a valid category.")

        if not date:
            errors.append("Date is required.")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                errors.append("Please enter a valid date (YYYY-MM-DD).")

        if errors:
            for msg in errors:
                flash(msg, "error")
            return redirect(url_for("edit_expense", id=id))

        conn = get_db()
        try:
            conn.execute(
                "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ?"
                " WHERE id = ?",
                (amount_val, category, date, description or "", id),
            )
            conn.commit()
        finally:
            conn.close()

        flash("Expense updated.", "success")
        return redirect(url_for("dashboard"))

    return render_template("expenses/edit.html", expense=expense, categories=CATEGORIES)


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = get_db()
    try:
        expense = conn.execute(
            "SELECT user_id FROM expenses WHERE id = ?", (id,)
        ).fetchone()
        if expense is None or expense["user_id"] != session["user_id"]:
            flash("Expense not found.", "error")
            return redirect(url_for("dashboard"))
        conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
        conn.commit()
    finally:
        conn.close()

    flash("Expense deleted.", "success")
    return redirect(url_for("dashboard"))


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
