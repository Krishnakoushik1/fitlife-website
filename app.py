from flask import Flask, render_template, request, redirect, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "fitness_secret_key"

# Required for Render (HTTPS)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True
)

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(
        "fitness.db",
        timeout=10,
        check_same_thread=False
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    db = get_db()
    try:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            height REAL,
            weight REAL,
            age INTEGER
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            time TEXT
        )
        """)
        db.commit()
    finally:
        db.close()


init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.execute(
                "SELECT id FROM users WHERE username=? AND password=?",
                (request.form["username"], request.form["password"])
            )
            user = cur.fetchone()
        finally:
            db.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/profile")

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (request.form["username"], request.form["password"])
            )
            db.commit()

            # ✅ THIS IS THE KEY LINE
            session["user_id"] = cur.lastrowid

            return redirect("/profile")

        except sqlite3.IntegrityError:
            return render_template(
                "register.html",
                error="Username already exists. Try logging in."
            )
        finally:
            db.close()

    return render_template("register.html")

# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                "UPDATE users SET height=?, weight=?, age=? WHERE id=?",
                (
                    request.form["height"],
                    request.form["weight"],
                    request.form["age"],
                    session["user_id"]
                )
            )
            db.commit()
        finally:
            db.close()

        return redirect("/steps")

    return render_template("profile.html")

# ---------------- STEPS ----------------
@app.route("/steps", methods=["GET", "POST"])
def steps():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        steps = int(request.form["steps"])
        calories = steps * 0.04
        weight_lost = calories / 7700

        badge = "🥉 Bronze Badge"
        if steps >= 10000:
            badge = "🏅 Gold Badge"
        elif steps >= 7000:
            badge = "🥈 Silver Badge"

        session["result"] = {
            "steps": steps,
            "calories": round(calories, 2),
            "weight_lost": round(weight_lost, 4),
            "badge": badge
        }
        return redirect("/diet")

    return render_template("steps.html")

# ---------------- DIET ----------------
@app.route("/diet")
def diet():
    if "result" not in session:
        return redirect("/steps")

    calories = session["result"]["calories"]
    plan = "High Protein Diet 🍗🥗" if calories > 300 else "Balanced Diet 🥗🍎"
    return render_template("diet.html", plan=plan)

# ---------------- QUOTES ----------------
@app.route("/quotes")
def quotes():
    if "user_id" not in session:
        return redirect("/")

    quotes_list = [
        "Small steps every day lead to big results. 💪",
        "Don’t stop when you’re tired. Stop when you’re done. 🔥",
        "Push yourself because no one else is going to do it for you.",
        "Success starts with self-discipline.",
        "Consistency beats motivation.",
        "A fit body, a calm mind, a fulfilled soul.",
        "Every step forward counts."
    ]

    return render_template("quotes.html", quote=random.choice(quotes_list))

# ---------------- RESULT ----------------
@app.route("/result")
def result():
    if "result" not in session:
        return redirect("/steps")
    return render_template("result.html", r=session["result"])

# ---------------- REMINDER ----------------
@app.route("/reminder", methods=["GET", "POST"])
def reminder():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    try:
        if request.method == "POST":
            db.execute(
                "INSERT INTO reminders (user_id, message, time) VALUES (?, ?, ?)",
                (session["user_id"], request.form["message"], request.form["time"])
            )
            db.commit()

        cur = db.execute(
            "SELECT message, time FROM reminders WHERE user_id=?",
            (session["user_id"],)
        )
        reminders = cur.fetchall()
    finally:
        db.close()

    return render_template("reminder.html", reminders=reminders)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- CONTACT ----------------
@app.route("/contact")
def contact():
    return render_template("contact.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)