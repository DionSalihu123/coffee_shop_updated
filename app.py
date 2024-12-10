from flask import Flask,render_template,request,url_for,redirect,session,jsonify 
from database import get_database
from werkzeug.security import generate_password_hash, check_password_hash 
from responses import get_response
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

def get_current_user():
    user = None

    if "emri" in session:
        user = session["emri"]
    return user 

@app.route("/")
@app.route("/home")
def home():
    username = get_current_user() 

    return render_template("index.html",username = username)



@app.route("/login", methods = ["POST", "GET"])
def login():
    user_name = get_current_user()

    error = None
    if request.method == "POST":
        username = request.form["username"]
        user_entered_password = request.form["password"] 

        db = get_database()

        user_info = db.execute("select * from users where username = ?", [username])

        user = user_info.fetchone()  

        if user:
            if check_password_hash(user["password"], user_entered_password): 
                session['user_id'] = user['id']  
                session['emri'] = user['username']
                return redirect(url_for("home")) 
            else:
                error = "please check your password!" 

    return  render_template("login.html", loginerror = error,user_name = user_name)


@app.route("/register", methods = ["POST", "GET"])
def register():
    user_name  = get_current_user()

    register_error = None 

    if request.method == "POST":
        username = request.form["username"] 
        lastname = request.form["lastname"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)  
        
        db = get_database() 
        
        check_user = db.execute("select * from users where username = ? or email = ?",[username,email]) 
        existing_user = check_user.fetchone()

        if existing_user: 
            if existing_user["username"] == username:
                register_error = "this username already exsist!" 
                return render_template("register.html",register_error = register_error)
            elif existing_user["email"] == email:
                register_error = "this email already exsist!"
                return render_template("register.html",register_error = register_error)


        db.execute("insert into users (username,lastname,email,password) values (? , ?, ?, ?)", [username,lastname,email,hashed_password])

        db.commit()

        return redirect(url_for("login")) 
    
    return  render_template("register.html",user_name  = user_name)




@app.route("/menu",methods = ["POST","GET"])
def menu():
    username = get_current_user()

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        item_name = request.form['item']
        item_price = request.form['price']

        db = get_database() 

        db.execute("insert into orders (user_id, item_name, item_price) values (?,?,?)",[session['user_id'],item_name,item_price])

        db.commit()


    return render_template("menu.html",username = username)
 


@app.route("/about")
def about():
    username = get_current_user()


    return render_template("about.html",username = username)


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    # Serve the chatbot UI on GET request
    if request.method == "GET":
        return render_template("index.html")  # Your chatbot HTML

    # Handle POST request and respond with a message
    if request.method == "POST":
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "Invalid request. 'message' is required."}), 400

        user_message = data["message"].lower()
        response = get_response(user_message) 
        return jsonify({"response": response})

    return render_template("index.html")



@app.route("/logout")
def logout():

    session.clear() 
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug = True)

