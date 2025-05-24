from flask import Flask, render_template, request, url_for, redirect, session, jsonify, abort, flash, g
from database import get_database, close_database
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Define upload folder
# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# Ensure database connections are closed after each request
app.teardown_appcontext(close_database)

def get_current_user():
    return session.get("emri")

def is_admin():
    if "user_id" not in session:
        return False
    db = get_database()
    user = db.execute("SELECT role FROM users WHERE id = ?", [session["user_id"]]).fetchone()
    return user and user["role"] == "admin"

def set_admin_user():
    db = get_database()
    username = "admin"
    try:
        db.execute("UPDATE users SET role = 'admin' WHERE username = ?", [username])
        db.commit()
        print(f"User {username} set as admin.")
    except sqlite3.Error as e:
        print(f"Error setting admin user: {e}")

@app.route("/")
@app.route("/home")
def home():
    username = get_current_user()
    return render_template("index.html", username=username, is_admin=is_admin())

@app.route("/login", methods=["POST", "GET"])
def login():
    user_name = get_current_user()
    error = None
    if request.method == "POST":
        username = request.form["username"]
        user_entered_password = request.form["password"]
        db = get_database()
        user_info = db.execute("SELECT * FROM users WHERE username = ?", [username])
        user = user_info.fetchone()

        if user and check_password_hash(user["password"], user_entered_password):
            session['user_id'] = user['id']
            session['emri'] = user['username']
            return redirect(url_for("home"))
        error = "Invalid username or password!"

    return render_template("login.html", loginerror=error, user_name=user_name)

@app.route("/register", methods=["POST", "GET"])
def register():
    user_name = get_current_user()
    register_error = None

    if request.method == "POST":
        username = request.form["username"]
        lastname = request.form["lastname"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        db = get_database()
        check_user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", [username, email])
        existing_user = check_user.fetchone()

        if existing_user:
            if existing_user["username"] == username:
                register_error = "This username already exists!"
            else:
                register_error = "This email already exists!"
            return render_template("register.html", register_error=register_error)

        db.execute("INSERT INTO users (username, lastname, email, password, role) VALUES (?, ?, ?, ?, ?)",
                   [username, lastname, email, hashed_password, "user"])
        db.commit()
        return redirect(url_for("login"))

    return render_template("register.html", user_name=user_name)

@app.route("/menu", methods=["POST", "GET"])
def menu():
    username = get_current_user()
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        item_name = request.form['item']
        item_price = request.form['price']
        db = get_database()
        db.execute("INSERT INTO orders (user_id, item_name, item_price) VALUES (?, ?, ?)",
                   [session['user_id'], item_name, item_price])
        db.commit()

    return render_template("menu.html", username=username)

@app.route("/about")
def about():
    username = get_current_user()
    return render_template("about.html", username=username)

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('login')) 

    db = get_database()
    users = db.execute("SELECT id, username, lastname, email, role FROM users").fetchall()
    products = db.execute("SELECT id, name, price, description, image FROM products").fetchall()

    if request.method == "POST":
        # Handle user actions
        user_id = request.form.get("user_id")
        if user_id:
            action = request.form.get("action")
            if action == "update_role":
                new_role = request.form.get("role")
                if new_role in ["user", "admin"]:
                    db.execute("UPDATE users SET role = ? WHERE id = ?", [new_role, user_id])
                    db.commit()
                    flash("User role updated.", "success")
            elif action == "delete":
                if int(user_id) != session["user_id"]:
                    db.execute("DELETE FROM users WHERE id = ?", [user_id])
                    db.commit()
                    flash("User deleted.", "success")
                else:
                    flash("You cannot delete yourself!", "danger")

    return render_template("admin.html", users=users, products=products, username=session.get("emri"), is_admin=is_admin())

@app.route("/admin/products/add", methods=["GET", "POST"])
def add_product():
    if not is_admin():
        return redirect(url_for('login'))
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image = request.files.get("image")
        if name and price:
            try:
                price = float(price)
                if price < 0:
                    flash("Price cannot be negative.", "danger")
                    return render_template("add_product.html", username=session.get("emri"), is_admin=is_admin())
                db = get_database()
                cursor = db.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", [name, price, description])
                db.commit()
                product_id = cursor.lastrowid
                if image and image.filename:
                    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        flash("Only PNG, JPG, and JPEG files are allowed.", "danger")
                        return render_template("add_product.html", username=session.get("emri"), is_admin=is_admin())
                    filename = secure_filename(f"{product_id}{os.path.splitext(image.filename)[1]}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(image_path)
                    db.execute("UPDATE products SET image = ? WHERE id = ?", [f'uploads/{filename}', product_id])
                    db.commit()
                flash("Product added successfully.", "success")
            except ValueError:
                flash("Invalid price value.", "danger")
            except sqlite3.Error as e:
                flash(f"Database error: {e}", "danger")
        else:
            flash("Name and price are required.", "danger")
        return redirect(url_for("admin_dashboard"))
    return render_template("add_product.html", username=session.get("emri"), is_admin=is_admin())

@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not is_admin():
        return redirect(url_for('login'))
    db = get_database()
    product = db.execute("SELECT id, name, price, description, image FROM products WHERE id = ?", [product_id]).fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image = request.files.get("image")
        existing_image = request.form.get("existing_image", product['image'])  # Retain existing image if no new upload
        if name and price:
            try:
                price = float(price)
                if price < 0:
                    flash("Price cannot be negative.", "danger")
                    return render_template("edit_product.html", product=product, username=session.get("emri"), is_admin=is_admin())
                image_path = existing_image
                if image and image.filename:
                    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        flash("Only PNG, JPG, and JPEG files are allowed.", "danger")
                        return render_template("edit_product.html", product=product, username=session.get("emri"), is_admin=is_admin())
                    filename = secure_filename(f"{product_id}{os.path.splitext(image.filename)[1]}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(image_path)
                    image_path = f'uploads/{filename}'
                db.execute("UPDATE products SET name = ?, price = ?, description = ?, image = ? WHERE id = ?",
                           [name, price, description, image_path, product_id])
                db.commit()
                flash("Product updated successfully.", "success")
            except ValueError:
                flash("Invalid price value.", "danger")
            except sqlite3.Error as e:
                flash(f"Database error: {e}", "danger")
        else:
            flash("Name and price are required.", "danger")
        return redirect(url_for("admin_dashboard"))
    return render_template("edit_product.html", product=product, username=session.get("emri"), is_admin=is_admin())

@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not is_admin():
        return redirect(url_for('login'))
    db = get_database()
    product = db.execute("SELECT id FROM products WHERE id = ?", [product_id]).fetchone()
    if product:
        db.execute("DELETE FROM products WHERE id = ?", [product_id])
        db.commit()
        flash("Product deleted successfully.", "success")
    else:
        flash("Product not found.", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", message="You do not have permission to access this page."), 403

if __name__ == "__main__":
    with app.app_context():
        set_admin_user()
    app.run(debug=True)