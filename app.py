from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "fitness_secret_key"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("fitness.db")

with get_db() as db:
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

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cur.fetchone()

        if user:
            session["user_id"] = user[0]
            return redirect("/profile")

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            return redirect("/")
        except:
            pass

    return render_template("register.html")

# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        height = request.form["height"]
        weight = request.form["weight"]
        age = request.form["age"]

        db = get_db()
        db.execute(
            "UPDATE users SET height=?, weight=?, age=? WHERE id=?",
            (height, weight, age, session["user_id"])
        )
        db.commit()
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

        if steps >= 10000:
            badge = "🏅 Gold Badge"
        elif steps >= 7000:
            badge = "🥈 Silver Badge"
        else:
            badge = "🥉 Bronze Badge"

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

    if calories > 300:
        plan = "High Protein Diet 🍗🥗"
    else:
        plan = "Balanced Diet 🥗🍎"

    return render_template("diet.html", plan=plan)


#------------------quotes-----------------
import random

@app.route("/quotes")
def quotes():
    if "user_id" not in session:
        return redirect("/")

    quotes_list = [
    "Small steps every day lead to big results. 💪",
    "Don’t stop when you’re tired. Stop when you’re done. 🔥",
    "Your body can stand almost anything. It’s your mind you have to convince.",
    "Push yourself because no one else is going to do it for you.",
    "Success starts with self-discipline.",
    "A one-hour workout is just 4% of your day.",
    "The pain you feel today will be the strength you feel tomorrow.",
    "Fitness is not about being better than someone else. It’s about being better than you used to be.",
    "Wake up. Work out. Look hot. Kick ass.",
    "Sweat is just fat crying. 😄",
    "No matter how slow you go, you are still lapping everyone on the couch.",
    "Train insane or remain the same.",
    "You don’t have to be extreme, just consistent.",
    "The body achieves what the mind believes.",
    "Exercise is a celebration of what your body can do.",
    "Once you see results, it becomes an addiction.",
    "Don’t wish for it. Work for it.",
    "Your only limit is you.",
    "Strong body. Strong mind.",
    "Fitness is a lifestyle, not a temporary fix.",
    "Every workout counts.",
    "The hardest lift is lifting yourself off the couch.",
    "Strive for progress, not perfection.",
    "When you feel like quitting, remember why you started.",
    "Sweat now, shine later.",
    "Fall in love with taking care of your body.",
    "You are stronger than you think.",
    "Make your body your strongest outfit.",
    "Discipline is choosing between what you want now and what you want most.",
    "Today’s effort is tomorrow’s confidence.",
    "Your future self will thank you.",
    "Be stronger than your excuses.",
    "Health is an investment, not an expense.",
    "If it doesn’t challenge you, it doesn’t change you.",
    "Workout because you love your body, not because you hate it."
      "A fit body, a calm mind, a fulfilled soul.",
    "One workout at a time.",
    "Excuses don’t burn calories.",
    "Fitness builds confidence.",
    "Consistency beats motivation.",
    "Your body hears everything your mind says.",
    "Strong habits create strong lives.",
    "Movement is medicine.",
    "Push harder than yesterday if you want a different tomorrow.",
    "Sweat is your body’s way of thanking you.",
    "The best project you’ll ever work on is you.",
    "Fitness is earned, not given.",
    "Believe in your strength.",
    "Every step forward counts."
    ]

    random_quote = random.choice(quotes_list)

    return render_template("quotes.html", quote=random_quote)



#-----------------logout-------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



# ---------------- RESULT ----------------
@app.route("/result")
def result():
    if "result" not in session:
        return redirect("/steps")

    return render_template("result.html", r=session["result"])

#-------------------contact-----------------

@app.route("/contact")
def contact():
    return render_template("contact.html")



# ---------------- REMINDER ----------------
@app.route("/reminder", methods=["GET", "POST"])
def reminder():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        message = request.form["message"]
        time = request.form["time"]

        db.execute(
            "INSERT INTO reminders (user_id, message, time) VALUES (?, ?, ?)",
            (session["user_id"], message, time)
        )
        db.commit()

    cur = db.execute(
        "SELECT message, time FROM reminders WHERE user_id=?",
        (session["user_id"],)
    )
    reminders = cur.fetchall()

    return render_template("reminder.html", reminders=reminders)

# ---------------- RUN ----------------
#if __name__ == "__main__":
  #  app.run(debug=True)

#-----------------execution-------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
