from flask import Flask,render_template,request,url_for,redirect,session 
from database import get_database
from werkzeug.security import generate_password_hash, check_password_hash 
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

def get_current_user():
    user = None
    #vlera defualt eshte none nuk nuk gjinder useri
    if "user" in session:
        user = session["user"]
        db = get_database()
        user_info = db.execute("select username from users where username = ?",[user]) 
        user = user_info.fetchone() 

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

        user_cursor = db.execute("select * from users where username = ?", [username])
        #e marrim vetem username sepese nese e marirm dhe passwordin kur e shikojm condition user['passord'] jemi duke  e marr passin plain text
        #dhe po e krahasojm me ate hashed shiko per me shume

        user = user_cursor.fetchone()  

        if user:
            if check_password_hash(user["password"], user_entered_password): 
                #nese perputhen passwodad e marrim ne session e krijojm nje key user_id dhe ja japim vleren e id
                session['user_id'] = user['id']  
                session['user'] = user['username']
                #getting the id from the databse beacuse the user is the var that is fetching the specific user from the db
                return redirect(url_for("home")) 
            else:
                error = "please check your password!" 

    return  render_template("login.html", loginerror = error,user_name = user_name)
#vlerat ne html i fergojm nga render_template


@app.route("/register", methods = ["POST", "GET"])
def register():
    user_name  = get_current_user()

    register_error = None 

    if request.method == "POST":
        #collect the user info from the forms
        username = request.form["username"] 
        password = request.form["password"]

        hashed_password = generate_password_hash(password)  
        
        #connect to database
        db = get_database() 
        
        check_user = db.execute("select * from users where username = ?",[username]) 
        existing_user = check_user.fetchone()

        if existing_user: 
            register_error = "this username already exsist!" 
            return render_template("register.html",register_error = register_error)


            #sql query to insert the data into the database
        db.execute("insert into users (username,password) values (? , ?)", [username,hashed_password])

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
 


@app.route("/logout")
def logout():

    session.clear() 
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug = True)

