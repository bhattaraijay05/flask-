from flask import Flask, render_template, request, session, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import json
import math
from datetime import datetime
import os
import re

with open("config.json", 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('LOCAL_URI')
db = SQLAlchemy(app)


class Contacts(db.Model):
    sn = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)


class Posts(db.Model):
    sn = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=True)


class Users(db.Model):
    sn = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(20), nullable=False)
    confirm_password = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.Integer, nullable=False, unique=True)
    date_created = db.Column(db.String(20), nullable=True)


@app.route('/')
@app.route('/main')
def main():
    posts = list(reversed(Posts.query.filter_by().all()))
    last = math.ceil(len(posts)/int(params["number_of_posts_per_page"]))
    # [0:params["number_of_posts_per_page"]]
    page = request.args.get('page')
    if not (str(page).isnumeric()):
        page = 1
    # pagination
    # First
    page = int(page)
    posts = posts[(page-1) * int(params["number_of_posts_per_page"]): (page-1) *
                  int(params["number_of_posts_per_page"]) + int(params["number_of_posts_per_page"])]
    #prev = #
    #next = page + 1
    if (page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)

    # last
    #prev = page - 1
    #next = #
    elif (page == last):
        prev = "/?page=" + str(page-1)
        next = "#"

    # middle
    #prev = page - 1
    #next = page + 1

    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)

    return render_template('mainbody.html', params=params, posts=posts, prev=prev, next=next)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        # Add database entry
        names = request.form.get('name')
        emails = request.form.get('email')
        phones = request.form.get('phone_num')
        messages = request.form.get('message')
        entry = Contacts(name=names, email=emails, phone=phones,
                         message=messages, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        flash("Your message has been submitted. We we'll get back to you soon", "success")
    return render_template('contact.html', params=params)


@app.route('/login', methods=['GET', 'POST'])
def loginuser():
    users = Users.query.all()
    for user in users:
        if ('user' in session and session['user'] == user.username):
            return render_template('profile.html', params=params)

    if request.method == "POST":
        username = request.form.get('usernames')
        password = request.form.get('passwords')
        if (username == user.username and password == user.password):
            session['user'] = user.username
            return render_template('profile.html', params=params, users=user.username, passs=user.password)
        else:
            flash(
                "No user exist with this username and password. Please double check the username and password", "danger")

    return render_template('userlogin.html', params=params)


def passwordValidation(password):
    passwd = password
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"

    # compiling regex
    pat = re.compile(reg)

    # searching regex
    mat = re.search(pat, passwd)

    if not mat:
        return False
    else:
        return True


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    users = Users.query.all()
    for user in users:
        if ('user' in session and session['user'] == user.username):
            return render_template('profile.html', params=params)

    if (request.method == 'POST'):
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        date = datetime.now()
        signingup = Users(first_name=first_name, last_name=last_name, username=username,
                          email=email, password=password, confirm_password=confirm_password, phone=phone, date_created=date)

        if (username == user.username or email == user.email):
            flash("User already exists with given details", "danger")
        elif(not passwordValidation(password)):
            flash(
                "Password is very weak, it must contain atleast 8 character with special symbols and numbers", "danger")
        elif(not phone.isnumeric()):
            flash("What kind of phone number is that", "danger")
        elif(password != confirm_password):
            flash("Passwords doesnot match", "danger")
        else:
            db.session.add(signingup)
            db.session.commit()
            flash("Thanks for signing up. Look your profile", "success")
            session['user'] = user.username
            return render_template('profile.html', params=params)
    return render_template('signup.html', params=params)


@app.route('/writecontent', methods=['GET', 'POST'])
def writecontent():
    if ('user' in session and session['user'] == os.getenv('ADMIN_USERNAME')):
        if (request.method == 'POST'):
            # Add database entry
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image = request.form.get('imagefile')
            date = datetime.now()
            post = Posts(title=title, slug=slug,
                         content=content, image=image, date=date)
            db.session.add(post)
            db.session.commit()
            flash("The post has been added successfully", "success")

        post = Posts.query.filter_by().all()
        return render_template('writecontent.html', params=params, post=post)
    return render_template('adminlogin.html', params=params)


@app.route('/content/<string:sn>', methods=['GET', 'POST'])
def content(sn):
    if ('user' in session and session['user'] == os.getenv('ADMIN_USERNAME')):
        if (request.method == 'POST'):
            # Add database entry
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image = request.form.get('imagefile')
            date = datetime.now()
            post = Posts.query.filter_by(sn=sn).first()
            post.title = title
            post.slug = slug
            post.content = content
            post.image = image
            db.session.commit()
            flash("The post has been edited successfully", "success")
            return redirect('/content/'+sn)
        post = Posts.query.filter_by(sn=sn).first()
        return render_template('content.html', params=params, post=post)
    return render_template('adminlogin.html', params=params)


@app.route('/delete/<string:sn>', methods=['GET', 'POST'])
def delete(sn):
    if ('user' in session and session['user'] == os.getenv('ADMIN_USERNAME')):
        post = Posts.query.filter_by(sn=sn).first()
        db.session.delete(post)
        db.session.commit()
        flash("The post has been deleted", "danger")
    return redirect('/admindashboard')


@app.route('/posts/<string:posts_slug>', methods=['GET'])
def posts_route(posts_slug):
    posts = Posts.query.filter_by(slug=posts_slug).all()
    return render_template('posts.html', params=params, posts=posts)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)
    return redirect(url_for('loginadmin'))


@app.route('/adminlogin', methods=['GET', 'POST'])
def loginadmin():
    if ('user' in session and session['user'] == os.getenv('ADMIN_USERNAME')):
        return render_template('content.html', params=params)

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if (username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD')):
            session['user'] = username
            return render_template('profile.html', params=params)
        flash("Enter the valid username and password", "danger")
    return render_template('adminlogin.html', params=params)


@app.route('/about/')
def about():
    return render_template('aboutus.html', params=params)


@app.route('/help/')
def help():
    return render_template('help.html', params=params)


@app.route('/admindashboard')
def admindashboard():
    if ('user' in session and session['user'] == os.getenv('ADMIN_USERNAME')):
        posts = Posts.query.filter_by().all()
        return render_template('admindashboard.html', params=params, posts=posts)
    return render_template('adminlogin.html', params=params)


app.run(debug=True)
