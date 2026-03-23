from flask import Flask,render_template,request,redirect,session,flash
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import mysql.connector
from datetime import timedelta
import os
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key="empsecretkey"
app.permanent_session_lifetime=timedelta(minutes=30)

UPLOAD_FOLDER='static/images/profile'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']='vishnusriamara@gmail.com'
app.config['MAIL_PASSWORD']='bqln fuwx ynsj zuoi'

mail=Mail(app)
s=URLSafeTimedSerializer(app.secret_key)

def get_db():
    return mysql.connector.connect(
    host="localhost",
    user='root',
    password='root',
    database='company'
   )

@app.route('/')
def Home():
    return render_template("register.html")

@app.route('/home')
def home1():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

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

@app.route('/register',methods=['POST'])
def register():
    id=request.form['id']
    username=request.form['username']
    password=request.form['password']
    role=request.form['role']
    email=request.form['email']

    conn=get_db()
    cursor=conn.cursor()
    check_query="select role from users where email=%s"
    cursor.execute(check_query,(email,))
    existing=cursor.fetchone()
    if existing:
        flash("Email already registered. Please login.", "danger")
        return redirect("/login")
    query="insert into users(id,username,password,role,email) values(%s,%s,%s,%s,%s)"
    cursor.execute(query,(id,username,password,role,email))
    conn.commit()
    cursor.close()
    flash("Registration Successful! Please login.", "success")
    return redirect("/login")
    

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logincheck",methods=['POST'])
def logincheck():
    username=request.form["username"]
    pwrd=request.form["pwrd"]
    session.permanent=True
    conn=get_db()
    cursor=conn.cursor(buffered=True)
    query="select * from users where username=%s and password=%s"
    cursor.execute(query,(username,pwrd))
    user=cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        session['user'] = user[1]
        session['profile_pic']=user[5] if user[5] else "default.png"
        return redirect("/dashboard")
    else:
        flash("Invalid username or password", "danger")
        return redirect("/login")
    
@app.route('/forgot_password')
def forget_password():
    return render_template("forgot_password.html")

@app.route('/send_reset_link',methods=["POST"])
def send_reset_link():
    email=request.form['email']
    conn=get_db()
    cursor=conn.cursor()
    query="select * from users where email=%s"
    cursor.execute(query,(email,))
    users=cursor.fetchone()
    if users:
        token=s.dumps(email,salt="Password-reset-salt")
        link=f"http://localhost:5000/reset_password/{token}"

        msg=Message("Password reset request",
                    sender="vishnusriamara@gmail.com",
                    recipients=[email])
        msg.body=f"click the link to reset your password:{link}"
        mail.send(msg)
        return redirect('/login')
    conn.commit()
    cursor.close()
    conn.close()
    flash("Email not registered. Please register first.", "danger")
    return redirect("/")

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
        query="update users set password=%s where email=%s"
        cursor=conn.cursor()
        cursor.execute(query,(new_password,email))
        conn.commit()
        cursor.close()
        flash("Password reset successful. Please login.", "success")
        return redirect("/login")
    return render_template("reset_password.html")

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
    cursor.close()
    return render_template("dashboard.html",total=total,dept=dept,max_salary=max_salary)
    
@app.route("/add_employee",methods=['GET','POST'])
def add_employee():
    if request.method=='POST':
        eid=request.form['eid']
        ename=request.form['ename']
        edept=request.form['edept']
        esalary=request.form['esalary']
        ephone=request.form['ephone']
        conn=get_db()
        query="insert into employee(eid,ename,edept,esalary,ephone) values(%s,%s,%s,%s,%s)"
        cursor=conn.cursor()
        cursor.execute(query,(eid,ename,edept,esalary,ephone))
        conn.commit()
        cursor.close()
        flash("Employee added successfully", "success")
        return redirect("/dashboard")
    return render_template('add_employee.html')

@app.route('/edit/<eid>')
def edit(eid):
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute("select * from employee where eid=%s",(eid,))
    data=cursor.fetchone()
    conn.commit()
    cursor.close()
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
    query="update employee set ename=%s,edept=%s,esalary=%s,ephone=%s where eid=%s"
    cursor.execute(query,(ename,edept,esalary,ephone,eid))
    conn.commit()
    cursor.close()
    flash("Employee updated successfully", "success")
    return redirect("/view_employee")

@app.route("/view_employee",methods=['GET','POST'])
def view_employee():
    conn=get_db()
    cursor=conn.cursor()
   
    if request.method=="POST":
        search=request.form['search']
        query="SELECT * FROM employee WHERE ename LIKE %s"
        cursor.execute(query,('%'+search+'%',))
    else:
        cursor.execute("SELECT * FROM employee")

    data=cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("view_employee.html",employee=data)

@app.route("/delete/<eid>")
def delete(eid):
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute("delete from employee where eid=%s",(eid,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/view_employee")

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    conn=get_db()
    cur=conn.cursor(buffered=True)
    cur.execute("SELECT * FROM users WHERE username=%s",(session['user'],))
    user=cur.fetchone()
    conn.close()
    cur.close()
    return render_template("profile.html",user=user)

@app.route('/edit_profile',methods=['GET','POST'])
def edit_profile():

    conn=get_db()
    cur=conn.cursor(buffered=True)

    if request.method=="POST":

        username=request.form['username']
        email=request.form['email']
        role=request.form['role']

        file=request.files.get('profile_pic')
        filename=None
        

        if file and file.filename!="":

            filename=secure_filename(file.filename)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

            cur.execute("UPDATE users SET username=%s,email=%s,role=%s,profile_pic=%s WHERE username=%s",
                        (username,email,role,filename,session['user']))
            session['profile_pic'] = filename
        else:
            cur.execute("UPDATE users SET username=%s,email=%s,role=%s WHERE username=%s",
                    (username,email,role,session['user']))

        conn.commit()

        flash("Profile updated successfully","success")

        return redirect('/profile')

    cur.execute("SELECT * FROM users WHERE username=%s",(session['user'],))
    user=cur.fetchone()
    cur.close()

    return render_template("edit_profile.html",user=user)
    

@app.route("/logout")
def logout():
    session.pop('user',None)
    session.pop('profile_pic',None)
    flash("Logged out successfully","info")
    return redirect("/login")   


if __name__=='__main__':
    app.run(debug=True)