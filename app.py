from flask import Flask,render_template,request,redirect,session,flash
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import sqlite3
from datetime import timedelta
import os
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key="empsecretkey"
app.permanent_session_lifetime=timedelta(minutes=30)

UPLOAD_FOLDER='static/images/profile'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Mail Config
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']='vishnusriamara@gmail.com'
app.config['MAIL_PASSWORD']='bqln fuwx ynsj zuoi'

mail=Mail(app)
s=URLSafeTimedSerializer(app.secret_key)

# SQLite DB Connection
def get_db():
    conn = sqlite3.connect("company.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- ROUTES ---------------- #

@app.route('/')
def Home():
    return render_template("register.html")

@app.route('/home')
def home1():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

# CONTACT
@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        purpose = request.form['purpose']
        message = request.form['message']

        msg = Message(
            subject=f"New Contact Request: {purpose}",
            sender=email,
            recipients=["vishnusriamara@gmail.com"]
        )

        msg.body = f"""
Name: {name}
Email: {email}
Purpose: {purpose}

Message:
{message}
"""
        mail.send(msg)

        reply = Message(
            subject="Thank You for Contacting Us",
            sender="vishnusriamara@gmail.com",
            recipients=[email]
        )

        reply.body = f"""
Hello {name},

Thank you for contacting us regarding: {purpose}.
We have received your message and will get back to you soon.

Your Message:
{message}

Best Regards,
Employee Management System Team
"""
        mail.send(reply)

        flash("Message sent successfully!", "success")
        return redirect('/contact')

    return render_template("contact.html")

# REGISTER
@app.route('/register',methods=['POST'])
def register():
    id=request.form['id']
    username=request.form['username']
    password=request.form['password']
    role=request.form['role']
    email=request.form['email']

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("SELECT role FROM users WHERE email=?", (email,))
    existing=cursor.fetchone()

    if existing:
        flash("Email already registered. Please login.", "danger")
        return redirect("/login")

    cursor.execute("INSERT INTO users(id,username,password,role,email) VALUES(?,?,?,?,?)",
                   (id,username,password,role,email))

    conn.commit()
    conn.close()

    flash("Registration Successful! Please login.", "success")
    return redirect("/login")

# LOGIN
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logincheck",methods=['POST'])
def logincheck():
    username=request.form["username"]
    pwrd=request.form["pwrd"]
    session.permanent=True

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username,pwrd))
    user=cursor.fetchone()

    conn.close()

    if user:
        session['user'] = user["username"]
        session['profile_pic']=user["profile_pic"] if user["profile_pic"] else "default.png"
        return redirect("/dashboard")
    else:
        flash("Invalid username or password", "danger")
        return redirect("/login")

# FORGOT PASSWORD
@app.route('/forgot_password')
def forget_password():
    return render_template("forgot_password.html")

@app.route('/send_reset_link',methods=["POST"])
def send_reset_link():
    email=request.form['email']

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    users=cursor.fetchone()

    if users:
        token=s.dumps(email,salt="Password-reset-salt")
        #link=f"http://localhost:5000/reset_password/{token}"
        link=request.host_url+"reset_password/"+token

        msg=Message("Password reset request",
                    sender="vishnusriamara@gmail.com",
                    recipients=[email])

        msg.body=f"Click the link to reset your password: {link}"
        mail.send(msg)

        conn.close()
        return redirect('/login')

    conn.close()
    flash("Email not registered. Please register first.", "danger")
    return redirect("/")

# RESET PASSWORD
@app.route('/reset_password/<token>',methods=['GET','POST'])
def reset_password(token):
    try:
        email=s.loads(token,salt='Password-reset-salt',max_age=500)
    except SignatureExpired:
        return "Link expired! Try again."

    if request.method=="POST":
        new_password=request.form['password']

        conn=get_db()
        cursor=conn.cursor()

        cursor.execute("UPDATE users SET password=? WHERE email=?", (new_password,email))

        conn.commit()
        conn.close()

        flash("Password reset successful. Please login.", "success")
        return redirect("/login")

    return render_template("reset_password.html")

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect("/login")

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employee")
    total=cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT edept) FROM employee")
    dept=cursor.fetchone()[0]

    cursor.execute("SELECT MAX(esalary) FROM employee")
    max_salary=cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html",total=total,dept=dept,max_salary=max_salary)

# ADD EMPLOYEE
@app.route("/add_employee",methods=['GET','POST'])
def add_employee():
    if request.method=='POST':
        eid=request.form['eid']
        ename=request.form['ename']
        edept=request.form['edept']
        esalary=request.form['esalary']
        ephone=request.form['ephone']

        conn=get_db()
        cursor=conn.cursor()

        cursor.execute("INSERT INTO employee(eid,ename,edept,esalary,ephone) VALUES(?,?,?,?,?)",
                       (eid,ename,edept,esalary,ephone))

        conn.commit()
        conn.close()

        flash("Employee added successfully", "success")
        return redirect("/dashboard")

    return render_template('add_employee.html')

# EDIT EMPLOYEE
@app.route('/edit/<eid>')
def edit(eid):
    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM employee WHERE eid=?", (eid,))
    data=cursor.fetchone()

    conn.close()

    return render_template("edit_employee.html",employee=data)

@app.route('/edit_employee',methods=["POST"])
def edit_employee():
    eid=request.form['eid']
    ename=request.form['ename']
    edept=request.form['edept']
    esalary=request.form['esalary']
    ephone=request.form['ephone']

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("""UPDATE employee 
                      SET ename=?,edept=?,esalary=?,ephone=? 
                      WHERE eid=?""",
                   (ename,edept,esalary,ephone,eid))

    conn.commit()
    conn.close()

    flash("Employee updated successfully", "success")
    return redirect("/view_employee")

# VIEW EMPLOYEE
@app.route("/view_employee",methods=['GET','POST'])
def view_employee():
    conn=get_db()
    cursor=conn.cursor()

    if request.method=="POST":
        search=request.form['search']
        cursor.execute("SELECT * FROM employee WHERE ename LIKE ?", ('%'+search+'%',))
    else:
        cursor.execute("SELECT * FROM employee")

    data=cursor.fetchall()
    conn.close()

    return render_template("view_employee.html",employee=data)

# DELETE EMPLOYEE
@app.route("/delete/<eid>")
def delete(eid):
    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("DELETE FROM employee WHERE eid=?", (eid,))

    conn.commit()
    conn.close()

    return redirect("/view_employee")

# PROFILE
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (session['user'],))
    user=cur.fetchone()

    conn.close()

    return render_template("profile.html",user=user)

# EDIT PROFILE
@app.route('/edit_profile',methods=['GET','POST'])
def edit_profile():
    conn=get_db()
    cur=conn.cursor()

    if request.method=="POST":
        username=request.form['username']
        email=request.form['email']
        role=request.form['role']

        file=request.files.get('profile_pic')

        if file and file.filename!="":
            filename=secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

            cur.execute("""UPDATE users 
                        SET username=?,email=?,role=?,profile_pic=? 
                        WHERE username=?""",
                        (username,email,role,filename,session['user']))
            session['profile_pic'] = filename
        else:
            cur.execute("""UPDATE users 
                        SET username=?,email=?,role=? 
                        WHERE username=?""",
                        (username,email,role,session['user']))

        conn.commit()

        # IMPORTANT FIX
        session['user'] = username

        conn.close()

        flash("Profile updated successfully","success")
        return redirect('/profile')

    cur.execute("SELECT * FROM users WHERE username=?", (session['user'],))
    user=cur.fetchone()

    conn.close()

    return render_template("edit_profile.html",user=user)

# LOGOUT
@app.route("/logout")
def logout():
    session.pop('user',None)
    session.pop('profile_pic',None)
    flash("Logged out successfully","info")
    return redirect("/login")

# RUN APP
if __name__=='__main__':
    app.run(debug=True)