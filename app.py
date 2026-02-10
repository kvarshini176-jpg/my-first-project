from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "sprint1_secure_key"

DB_NAME = "database.db"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        name TEXT,
        dob TEXT,
        address TEXT,
        kyc TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS wallet (
        user_id INTEGER,
        balance INTEGER
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item TEXT,
        price INTEGER,
        quantity INTEGER
    )
    """)

    db.commit()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        otp = request.form["otp"]

        if otp != "123456":
            return redirect("/")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")

        return redirect("/")

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        db.execute(
            "INSERT INTO users(username, password, kyc) VALUES (?,?,?)",
            (username, password, "Pending")
        )

        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO wallet(user_id, balance) VALUES (?,?)", (user_id, 0))
        db.commit()

        return redirect("/")

    return render_template("register.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        name = request.form["name"]
        dob = request.form["dob"]
        address = request.form["address"]

        db.execute("""
        UPDATE users
        SET name=?, dob=?, address=?, kyc=?
        WHERE id=?
        """, (name, dob, address, "Pending", session["user_id"]))

        db.commit()

    user = db.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    return render_template("profile.html", user=user)

# ---------------- WALLET ----------------
@app.route("/wallet", methods=["GET", "POST"])
def wallet():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        amount = int(request.form["amount"])
        db.execute(
            "UPDATE wallet SET balance = balance + ? WHERE user_id=?",
            (amount, session["user_id"])
        )
        db.commit()

    wallet = db.execute(
        "SELECT * FROM wallet WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()

    return render_template("wallet.html", wallet=wallet)

# ---------------- CART ----------------
@app.route("/cart", methods=["GET", "POST"])
def cart():
    if "user_id" not in session:
        return redirect("/")

    message = None
    db = get_db()

    if request.method == "POST":
        total = int(request.form["total"])
        wallet_amount = int(request.form["wallet"])

        wallet = db.execute(
            "SELECT balance FROM wallet WHERE user_id=?",
            (session["user_id"],)
        ).fetchone()

        if wallet["balance"] >= wallet_amount:
            db.execute(
                "UPDATE wallet SET balance = balance - ? WHERE user_id=?",
                (wallet_amount, session["user_id"])
            )
            db.commit()

            remaining = total - wallet_amount
            message = f"Order successful! Wallet ₹{wallet_amount}, Remaining ₹{remaining} via Bank/Card"
        else:
            message = "Insufficient wallet balance"

    return render_template("cart.html", message=message)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)