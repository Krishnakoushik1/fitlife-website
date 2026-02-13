from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import random

app = Flask(__name__)
app.secret_key = "fitness_secret_key"

# ---------------- DATABASE CONFIG ----------------

DATABASE_URL = os.environ.get("postgresql://postgres_koushik_user:EbxNI3v6HXaLyDuW2Rc7otyoyTvAV45U@dpg-d67n8ip4tr6s739g5s00-a.singapore-postgres.render.com/postgres_koushik")

if DATABASE_URL:
    # Render PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SESSION_COOKIE_SECURE"] = True
else:
    # Local SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fitness.db"
    app.config["SESSION_COOKIE_SECURE"] = False

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    age = db.Column(db.Integer)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(200))
    time = db.Column(db.String(50))

# Create tables
with app.app_context():
    db.create_all()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("profile"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(username=request.form["username"]).first():
            return render_template("register.html", error="Username already exists")

        new_user = User(
            username=request.form["username"],
            password=request.form["password"]
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        return redirect(url_for("profile"))

    return render_template("register.html")

# ---------------- PROFILE ----------------

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.height = request.form["height"]
        user.weight = request.form["weight"]
        user.age = request.form["age"]
        db.session.commit()
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

# ---------------- REMINDER ----------------

@app.route("/reminder", methods=["GET", "POST"])
def reminder():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_reminder = Reminder(
            user_id=session["user_id"],
            message=request.form["message"],
            time=request.form["time"]
        )
        db.session.add(new_reminder)
        db.session.commit()

    reminders = Reminder.query.filter_by(user_id=session["user_id"]).all()

    return render_template("reminder.html", reminders=reminders)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not DATABASE_URL)
