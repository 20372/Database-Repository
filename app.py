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

def is_logged_in_teacher():
        email = session.get("email")
        con = create_connection(DATABASE)
        cur = con.cursor()
        query = """SELECT is_teacher FROM users_table WHERE email = ?"""
        cur.execute(query, (email, ))
        teacher = cur.fetchall()
        con.close()
        print("yooo", teacher)
        if ('yes',) in teacher:
            print("teacher logged in!")
            con = create_connection(DATABASE)
            query = "SELECT users_id FROM users_table"
            cur = con.cursor()
            cur.execute(query)
            test = cur.fetchall()
            print(test)

            return True
        else:
            return False
@app.route('/')
def render_home():
    return render_template('home.html', logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())

@app.route('/home')
def render_home_page():
    return render_template('home.html', logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())


@app.route('/dictionary_page', methods=['GET'])
def render_dictionary_page():
    if is_logged_in_teacher():
        print("Teacher if logged in!")

    search = request.args.get('search', '').lower().strip() #args stops attributeError by returning an empty string before you search something
    con = create_connection(DATABASE)
    query = "SELECT cat_id, category_name FROM category_table"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()

    if search:    #search function
        query2 = """SELECT word_id, english_word, te_reo_word, category_name FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id WHERE english_word LIKE ? OR te_reo_word LIKE ?"""
        cur.execute(query2, ('%' + search + '%', '%' + search + '%'))
    else:     #if no search term gets every word from the database and displays that instead
        query2 = """SELECT word_id, english_word, te_reo_word, category_name FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id"""
        cur.execute(query2)

    word = cur.fetchall()
    con.close()

    return render_template('dictionary_page.html', logged_in=is_logged_in(), categories=category_list, words=word,teacher_log=is_logged_in_teacher())
@app.route('/word_info/<word_id>')
def render_word_info(word_id):
    if is_logged_in_teacher():
        print("Teacher if logged in!")
    con = create_connection(DATABASE)
    query = "SELECT english_word, te_reo_word, category_name, levels, user_fk, description FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id WHERE table_word.word_id = ?"
    cur = con.cursor()
    cur.execute(query, (word_id,))
    word = cur.fetchall()
    con.close()
    return render_template('word_info.html', logged_in = is_logged_in(), words=word, teacher_log = is_logged_in_teacher())



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
    return render_template("login.html", logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())

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
        teacher = request.form.get("teacher")

        if password != password2:
            return redirect("/signup?error='Passwords do not match.")
        if len(password) < 8:
            return redirect("/signup?error='Password must be at least 8 characters.")

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO users_table (f_name, l_name, email, password, is_teacher) VALUES (?,?,?,?,?)"
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, hashed_password, teacher))
            con.commit()
        except sqlite3.IntegrityError:
            con.close()
            return redirect("/signup?error='Email is already in use.")

        con.commit()
        con.close()

        return redirect("/login")
    return render_template("signup.html", logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())

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


    return render_template('editor.html', logged_in = is_logged_in(), categories=category_list, teacher_log = is_logged_in_teacher())

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
        english_word = request.form.get('english_word').lower().strip()
        te_reo_word = request.form.get('te_reo_word').lower().strip()
        description = request.form.get('description').lower().strip()
        category = request.form.get('cat_id').lower().strip()
        category_split = category.split(", ")
        cat_fk = category_split[0].title()
        print(category)
        level = request.form.get('level').lower().strip()
        users_fk = request.form.get('')
        con = create_connection(DATABASE)
        query = "INSERT INTO table_word (english_word, te_reo_word, description, cat_fk, level, users_fk ) VALUES (?, ?, ?, ?, ?, ?)"

        cur = con.cursor()
        words = (english_word, te_reo_word, description, cat_fk, level, users_fk)
        cur.execute(query, words)
        con.commit()
        con.close()
        return redirect('/editor')

@app.route('/delete_word', methods=['POST', 'GET'])
def render_delete_word():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    if request.method == 'POST':
        word_id = request.form.get('word_id')
        print(word_id)
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute('SELECT * FROM table_word WHERE word_id = ?', (word_id,))
        row = cur.fetchone()
        if row is None:
            return redirect('/editor?word_id+is+not+valid')
        word_name = row[1]
        print(word_name)
        con.close()

        return render_template("delete_confirm.html", id=word_id, name=word_name, type="word")

    return redirect('/editor')

@app.route('/delete_word_confirm/<word_id>')
def render_delete_word_confirm(word_id):
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    con = create_connection(DATABASE)
    query = "DELETE FROM table_word WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (word_id,))
    con.commit()
    con.close()
    return redirect("/editor")


app.run(host='0.0.0.0', debug=True)
