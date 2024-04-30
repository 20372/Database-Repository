from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt



DATABASE = ""
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "ufbbwu19274"
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    if session.get("email") is None:
        print("not loggied in ")
        return False
    else:
        print("logged in!")
        return True

@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in = is_logged_in())


@app.route('/menu/cat_id>')
def render_menu_page(cat_id):
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, image, price FROM products WHERE cat_id=?>"
    cur = con.cursor()
    cur.execute(query, (cat_id, ))
    product_list = cur.fetchall()
    query = "SELECT id, name FROM category"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    print(product_list)
    return render_template('menu.html', products=product_list, categories=category_list)


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in = is_logged_in())

@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():
        return redirect('/menu/1')
    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM user WHERE email = ?"""
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email, ))
        user_data = cur.fetchone()
        con.close()

        try:
            user_id = user_data[0]
            first_name = user_data[1]
            db_password = user_data[2]
        except IndexError:
            return redirect("/login?error=Invalid+username+or+password")
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')

        session['email'] = email
        session['userid'] = user_id
        session['firstname'] = first_name
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in = is_logged_in())

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if is_logged_in():
        return redirect('/menu/1')
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect("/signup?error='Passwords do not match.")
        if len(password) < 8:
            return redirect("/signup?error='Password must be at least 8 characters.")

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO user (fname, lname, email, password) VALUES (?,?,?,?)"
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, hashed_password))
            con.commit()
        except sqlite3.IntegrityError:
            con.close()
            return redirect("/signup?error='Email is already in use.")

        con.commit()
        con.close()

        return redirect("/login")
    return render_template("signup.html", logged_in = is_logged_in())

@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect("/?message=See+you+next+time!")

app.run(host='0.0.0.0', debug=True)