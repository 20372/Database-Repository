from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error           #imports extra modules I need for my code
from flask_bcrypt import Bcrypt



DATABASE = "identifier.sqlite"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "ufbbwu19274" #key used for encrypting the password
def create_connection(db_file): #connects to the database
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)   #prints the error message
    return None


def is_logged_in():    #checks if the user has logged in
    if session.get("email") is None:
        print("not logged in ")
        return False
    else:
        print("logged in!")
        return True

@app.route('/')
def render_home():
    return render_template('home.html', logged_in = is_logged_in())

@app.route('/home')
def render_home_page():
    return render_template('home.html', logged_in = is_logged_in())

@app.route('/menu/cat_id>')
def render_menu_page(cat_id):
    con = create_connection(DATABASE)  #uses the create_connection function to make a variable to access the database
    query = "SELECT name, description, volume, image FROM products WHERE cat_id=?>" #Getting the information needed from the database
    cur = con.cursor()
    cur.execute(query, (cat_id, ))
    product_list = cur.fetchall()
    query = "SELECT id, name FROM category"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close() #closes the connection to the database
    print(product_list)
    return render_template('menu.html', products=product_list, categories=category_list)


@app.route('/dictionary_page')
def render_dictionary_page():
    return render_template('dictionary_page.html', logged_in = is_logged_in())

@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in(): #uses the is login function to check if user is logged in
        return redirect('/home')
    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = """SELECT users_id, f_name, password FROM users_table WHERE email = ?"""  #gets id, first name and password from the database
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email, ))
        user_data = cur.fetchone()
        con.close()   #closes the connection to the database

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
        return redirect('/home')
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
        query = "INSERT INTO users_table (f_name, l_name, email, password) VALUES (?,?,?,?)"
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

@app.route('/editor')
def editor():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+thanks')
    con = create_connection(DATABASE)
    query = "SELECT cat_id, category_name FROM category_table"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()


    return render_template('editor.html', logged_in = is_logged_in(), categories=category_list)

@app.route('/add_category', methods=['POST', 'GET'])
def add_category():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    if request.method == 'POST':
        print(request.form)
        cat_name = request.form.get('name').lower().strip()
        print(cat_name)
        con = create_connection(DATABASE)
        query = "INSERT INTO category_table (category_name) VALUES (?)"
        cur = con.cursor()
        cur.execute(query, (cat_name, ))
        con.commit()
        con.close()
        return redirect('/editor')

@app.route('/delete_category', methods=['POST', 'GET'])
def render_delete_category():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    if request.method == 'POST':
        category = request.form.get('cat_id')
        print(category)
        category = category.split(", ")
        cat_id = category[0]
        cat_name = category[1]
        return render_template("delete_confirm.html", id=cat_id, name=cat_name, type="category")

    return redirect('/editor')

@app.route('/delete_category_confirm/<cat_id>')
def render_delete_category_confirm(cat_id):
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    con = create_connection(DATABASE)
    query = "DELETE FROM category_table WHERE cat_id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id, ))
    con.commit()
    con.close()
    return redirect("/editor")

@app.route('/add_word', methods=['POST', 'GET'])
def add_word():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    if request.method == 'POST':
        print(request.form)
        words = request.form.get('english_word, te_reo_word, description, category, level').lower().strip()
        print(words)
        con = create_connection(DATABASE)
        query = "INSERT INTO table_word (english_word, te_reo_word, description, category, level ) VALUES (? ? ? ? ?)"
        cur = con.cursor()
        cur.execute(query, words, )
        con.commit()
        con.close()
        return redirect('/editor')



app.run(host='0.0.0.0', debug=True)
