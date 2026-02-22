from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simulated Users Database
users_db = {
    "user1": {
        "username": "user1",
        "password": "pass1",
        "phone": "9999999999",
        "balance": 5000,
        "bank_balance": 10000,
        "kyc_uploaded": False
    }
}

# Products
products_db = {
    1: {"name": "Phone", "price": 12000},
    2: {"name": "Headset", "price": 1500},
    3: {"name": "Charger", "price": 500},
}

# Session timeout
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)


# ---------- LOGIN / REGISTER / OTP ----------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("All fields are required!")
            return redirect(url_for("login"))
        user = users_db.get(username)
        if user and user["password"] == password:
            session['user'] = username
            flash("Login successful!")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        phone = request.form.get("phone")
        if not username or not password or not phone:
            flash("All fields are required!")
            return redirect(url_for("register"))
        if username in users_db:
            flash("User already exists!")
            return redirect(url_for("register"))
        users_db[username] = {
            "username": username,
            "password": password,
            "phone": phone,
            "balance": 0,
            "bank_balance": 10000,
            "kyc_uploaded": False
        }
        flash("Registration successful! Login now.")
        return redirect(url_for("login"))
    return render_template("register.html")

# ---------- FORGOT PASSWORD ----------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get("username")
        if not username:
            flash("Please enter your username!")
            return redirect(url_for("forgot_password"))
        if username in users_db:
            flash(f"User found. Reset your password below.")
            return redirect(url_for("reset_password", username=username))
        else:
            flash("Username does not exist!")
            return redirect(url_for("forgot_password"))
    return render_template("forgot_password.html")


@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if username not in users_db:
        flash("Invalid reset link!")
        return redirect(url_for("login"))
    if request.method == 'POST':
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if not new_password or not confirm_password:
            flash("All fields are required!")
            return redirect(url_for("reset_password", username=username))
        if new_password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for("reset_password", username=username))
        users_db[username]["password"] = new_password
        flash("Password reset successful! Login now.")
        return redirect(url_for("login"))
    return render_template("reset_password.html", username=username)


@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("Logged out successfully!")
    return redirect(url_for("login"))


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    user = users_db[session["user"]]
    return render_template("dashboard.html", user=user)


# ---------- SHOP ----------
@app.route('/shop')
def shop():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    return render_template("shop.html", products=products_db)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    cart = session.get("cart", [])
    for item in cart:
        if item["id"] == product_id:
            item["quantity"] += 1
            break
    else:
        product = products_db[product_id]
        cart.append({"id": product_id, "name": product["name"], "price": product["price"], "quantity": 1})
    session["cart"] = cart
    session.modified = True
    flash(f"{products_db[product_id]['name']} added to cart!")
    return redirect(url_for("cart"))


# ---------- CART ----------
@app.route('/cart')
def cart():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    items = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in items)
    return render_template("cart.html", items=items, total=total)


@app.route('/update_cart/<int:product_id>/<action>')
def update_cart(product_id, action):
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    cart = session.get("cart", [])
    for item in cart:
        if item["id"] == product_id:
            if action == "increase":
                item["quantity"] += 1
            elif action == "decrease" and item["quantity"] > 1:
                item["quantity"] -= 1
            elif action == "delete":
                cart.remove(item)
            break
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


# ---------- PROFILE ----------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    user = users_db[session["user"]]
    if request.method == 'POST':
        username = request.form.get("username")
        phone = request.form.get("phone")
        if username and phone:
            user["username"] = username
            user["phone"] = phone
            flash("Profile updated successfully!")
        else:
            flash("All fields required!")
        users_db[session["user"]] = user
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)


# ---------- WALLET ----------
@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    user = users_db[session["user"]]
    if request.method == "POST":
        amount = float(request.form.get("amount", 0))
        method = request.form.get("method")
        if method == "bank":
            if amount > user["bank_balance"]:
                flash("Insufficient bank balance!")
            else:
                user["bank_balance"] -= amount
                user["balance"] += amount
                flash(f"₹{amount} added from Bank!")
        elif method == "card":
            # Simulated card always succeeds
            user["balance"] += amount
            flash(f"₹{amount} added from Credit Card!")
    users_db[session["user"]] = user
    return render_template("wallet.html", user=user)


# ---------- KYC ----------
@app.route('/kyc', methods=['GET', 'POST'])
def kyc():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))
    user = users_db[session["user"]]
    if request.method == "POST":
        file = request.files.get("kyc_file")
        if file:
            filename = f"{user['username']}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user["kyc_uploaded"] = True
            flash("KYC Uploaded Successfully!")
    users_db[session["user"]] = user
    return render_template("kyc.html", user=user)


# ---------- RUN APP ----------
if __name__ == '__main__':
    app.run(debug=True)
