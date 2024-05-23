from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error           #imports extra modules I need for my code
from flask_bcrypt import Bcrypt



DATABASE = "identifier.sqlite"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "ufbbwu19274"
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
        print("logged in!")  #returns true if they are logged in
        return True

def is_logged_in_teacher():   #checks if a teacher account has logged in
        email = session.get("email")
        con = create_connection(DATABASE)
        cur = con.cursor()
        query = """SELECT is_teacher FROM users_table WHERE email = ?"""  #selects is_teacher from database
        cur.execute(query, (email, ))
        teacher = cur.fetchall()
        con.close()
        if ('yes',) in teacher:
            print("teacher logged in!")
            return True  #returns true if a teacher is logged in
        else:
            return False #if teacher is not logged in returns false
@app.route('/')
def render_home():
    return render_template('home.html', logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())

@app.route('/home')  #app route for my home.html page
def render_home_page():
    return render_template('home.html', logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())


@app.route('/sort_by_category/<cat_id>', methods=['POST', 'GET'])  #When users click on a category it sorts the table by the category
def render_sort_by_category_page(cat_id):  #uses catgory id to sort the table
    if is_logged_in_teacher():
        print("Teacher if logged in!")
    con = create_connection(DATABASE)

    query = "SELECT cat_id, category_name FROM category_table"  #selects the category_name from table used for updating the catogory list.
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()

    cur = con.cursor()  #selects the words needed from both tables and uses inner join to combine them
    query = """SELECT word_id, english_word, te_reo_word, category_name FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id WHERE cat_id = ?"""
    cur.execute(query, (cat_id,))
    word = cur.fetchall()
    con.close() #words is used to display the words infomation in the html code e.g te_reo_word and english_word
    return render_template('sort_by_category.html', logged_in=is_logged_in(), words=word,teacher_log=is_logged_in_teacher(), categories=category_list) #categories variable is used in the html to display new category when they get addedd



@app.route('/dictionary_page', methods=['POST','GET'])
def render_dictionary_page():
    if is_logged_in_teacher():
        print("Teacher if logged in!")

    search = request.args.get('search', '').lower().strip() #args stops attributeError by returning an empty string before you search something
    con = create_connection(DATABASE)
    query = "SELECT cat_id, category_name FROM category_table" #same as above
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()

    if search:    #search function #selects the information from both tables and uses inner join to combine into one table - enlgish word like ? or teo_reo_word like ? allows users to sort by both enlish and maori words
        query2 = """SELECT word_id, english_word, te_reo_word, category_name FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id WHERE english_word LIKE ? OR te_reo_word LIKE ?"""
        cur.execute(query2, ('%' + search + '%', '%' + search + '%'))
    else:     #if no search term gets every word from the database and displays that instead
        query2 = """SELECT word_id, english_word, te_reo_word, category_name FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id""" #display the whole table if no search occurs
        cur.execute(query2)

    word = cur.fetchall()
    con.close()

    return render_template('dictionary_page.html', logged_in=is_logged_in(), categories=category_list, words=word,teacher_log=is_logged_in_teacher()) #cateogires and word are used same way as sort by categories page
@app.route('/word_info/<word_id>') #the function runs when user clicks on a word - shows them extra details about that word
def render_word_info(word_id):
    if is_logged_in_teacher():
        print("Teacher if logged in!")
    con = create_connection(DATABASE) #selects all the inforamtion (e.g image,date,level) form both tables
    query = "SELECT word_id, english_word, te_reo_word, category_name, levels, description, word_date, image FROM table_word INNER JOIN category_table ON table_word.cat_fk = cat_id WHERE table_word.word_id = ?"
    cur = con.cursor()

    try:
        cur.execute(query, (word_id,))
        word = cur.fetchall()
    except Exception as e:
        print(e)

    query2 = "SELECT f_name, l_name FROM table_word INNER JOIN users_table ON users_table.users_id = table_word.user_fk WHERE word_id = ?"
    try:
        cur.execute(query2, (word_id,))  #user_name is used to display the user of entry in the html page
        user_name = cur.fetchall()
        print(user_name)
    except Exception as e:
        print(e)


    con.close()  #closes the connection to the database
    return render_template('word_info.html', logged_in = is_logged_in(), words=word, teacher_log = is_logged_in_teacher(), user=user_name)



@app.route('/login', methods=['POST', 'GET'])  #login function used to login to a account
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
            return redirect("/login?error=Invalid+username+or+password")  #returns a error message if username + password are invalid
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect') #returns a error message if username or password is wrong

        session['email'] = email
        session['userid'] = user_id
        session['firstname'] = first_name
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in = is_logged_in(), teacher_log = is_logged_in_teacher())

@app.route('/signup', methods=['POST', 'GET'])  #sigup function used creating a teacher or student account
def render_signup():
    if is_logged_in():
        return redirect('/home')
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')  #request.form.get gets the users input and saves it as a variable
        password2 = request.form.get('password2')
        teacher = request.form.get("teacher")

        if password != password2:
            return redirect("/signup?error='Passwords do not match.")  #if passwrod dont match return a error message
        if len(password) < 8:
            return redirect("/signup?error='Password must be at least 8 characters.")  #if password is less then 8 letters returns a error message

        hashed_password = bcrypt.generate_password_hash(password) #encrpts the password
        con = create_connection(DATABASE)
        query = "INSERT INTO users_table (f_name, l_name, email, password, is_teacher) VALUES (?,?,?,?,?)"  #saves the new information in the users table
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

@app.route('/logout')  #logout function redirects you to home page when you logout
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect("/?message=See+you+next+time!")

@app.route('/editor')  #editor function selects the most recent category information and displays the webpage
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

@app.route('/add_category', methods=['POST', 'GET'])  #add_cateogry inserts the users input into the database and redirect users back to editor page
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

@app.route('/delete_category', methods=['POST', 'GET']) #delete_category pass the users input to delete_cateogry_confirm page if user clicks yes
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

@app.route('/delete_category_confirm/<cat_id>')  #function deletes the cateogryr fomr the database table and redirects the user back to the editor
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

@app.route('/add_word', methods=['POST', 'GET'])  #function gets users input and saves it into the table_word table beofre redirectesd them back to the editor
def add_word():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    if request.method == 'POST':
        print(request.form)
        english_word = request.form.get('english_word').lower().strip()
        te_reo_word = request.form.get('te_reo_word').lower().strip()
        description = request.form.get('description').lower().strip()
        word_date = request.form.get('word_date').lower().strip()
        user_fk = request.form.get('user').lower().strip()
        category = request.form.get('cat_id').lower().strip() #gets users input
        category_split = category.split(", ")
        cat_fk = category_split[0].title()
        level = request.form.get('level').lower().strip()
        con = create_connection(DATABASE)
        query = "INSERT INTO table_word (english_word, te_reo_word, description, levels, cat_fk, user_fk, word_date) VALUES (?, ?, ?, ?, ?, ?, ?)" #inserts the data

        cur = con.cursor()
        words = (english_word, te_reo_word, description, level, cat_fk, user_fk, word_date)  #executes the query
        cur.execute(query, words)
        con.commit()
        con.close()
        return redirect('/editor') #sends user to admin page

@app.route('/delete_word', methods=['POST', 'GET']) #function is used for deleting words from the database
def render_delete_word():
    if not is_logged_in():
        return redirect('//?message=Need+to+be+logged+in+')
    if request.method == 'POST':
        word_id = request.form.get('word_id')  #gets word_id entered by the user (user input)
        print(word_id)
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute('SELECT word_id, english_word, te_reo_word FROM table_word WHERE word_id = ?', (word_id,))
        row = cur.fetchone()
        if row is None:
            return redirect('/editor?word_id+is+not+valid')
        word_name = row[1]  #pass the word onto the delete word confirm page
        print(word_name)
        con.close()

        return render_template("delete_confirm.html", id=word_id, name=word_name, type="word")

    return redirect('/editor')

@app.route('/delete_word_confirm/<word_id>')  #delete word confirm page, function is used for deleting the word from the database based on the word_id
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
