from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "fitness_secret_key"

# ---------------- ENVIRONMENT DETECTION ----------------
# If running on Render/Production, PORT variable exists
IS_PRODUCTION = os.environ.get("PORT") is not None

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION  # True only in production (HTTPS)
)

# ---------------- DATABASE ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fitness.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT DATABASE ----------------
def init_db():
    db = get_db()
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
    db.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        ).fetchone()
        db.close()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))
        else:
            return render_template("login.html", error="Invalid credentials")

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

            session["user_id"] = cur.lastrowid
            db.close()
            return redirect(url_for("profile"))

        except sqlite3.IntegrityError:
            db.close()
            return render_template("register.html", error="Username already exists")

    return render_template("register.html")

# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        db = get_db()
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
        db.close()
        return redirect(url_for("steps"))

    return render_template("profile.html")

# ---------------- STEPS ----------------
@app.route("/steps", methods=["GET", "POST"])
def steps():
    if "user_id" not in session:
        return redirect(url_for("login"))

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

        return redirect(url_for("diet"))

    return render_template("steps.html")

# ---------------- DIET ----------------
@app.route("/diet")
def diet():
    if "result" not in session:
        return redirect(url_for("steps"))

    calories = session["result"]["calories"]
    plan = "High Protein Diet 🍗🥗" if calories > 300 else "Balanced Diet 🥗🍎"

    return render_template("diet.html", plan=plan)

# ---------------- RESULT ----------------
@app.route("/result")
def result():
    if "result" not in session:
        return redirect(url_for("steps"))
    return render_template("result.html", r=session["result"])

# ---------------- QUOTES ----------------
@app.route("/quotes")
def quotes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    quotes_list = [
        "Small steps every day lead to big results. 💪",
        "Consistency beats motivation.",
        "Push yourself because no one else will.",
        "Success starts with discipline.",
        "Every step forward counts."
    ]

    return render_template("quotes.html", quote=random.choice(quotes_list))

# ---------------- REMINDER ----------------
@app.route("/reminder", methods=["GET", "POST"])
def reminder():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":
        db.execute(
            "INSERT INTO reminders (user_id, message, time) VALUES (?, ?, ?)",
            (session["user_id"], request.form["message"], request.form["time"])
        )
        db.commit()

    reminders = db.execute(
        "SELECT message, time FROM reminders WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    db.close()
    return render_template("reminder.html", reminders=reminders)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not IS_PRODUCTION)
