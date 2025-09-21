from flask import render_template, flash, redirect, url_for, request
from app import app
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User
from urllib.parse import urlsplit
from datetime import datetime, timezone
from app.models import Task  # Added for Study Planner



# study planner homepage
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route("/pomodoro_timer")
def pomodoro_timer():
    return render_template("pomodoro_timer.html")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': '67'},
        {'author': user, 'body': 'hi'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',form=form)


    
@app.route('/study_planner')
def study_planner():
    tasks = Task.query.order_by(Task.due_date).all() # query/get data from database sorted by due date
    return render_template('study_planner.html', tasks=tasks) # call study planner

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        subject = request.form['subject']
        description = request.form['description']
        due_date = request.form['due_date']
        new_task = Task(subject=subject, description=description, due_date=due_date)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('study_planner'))
    return render_template('add_task.html')

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('study_planner'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('study_planner'))
