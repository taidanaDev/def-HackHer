from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website.models import Note, Task
from website import db
import json
import datetime

views = Blueprint('views', __name__)


# Home route with notes and calendar functionality
@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')  # Gets the note from the HTML form

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)  # Creating a new note
            db.session.add(new_note)  # Adding the note to the database
            db.session.commit()
            flash('Note added!', category='success')

    # Pass tasks for the calendar
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", user=current_user, tasks=tasks)


# Route to delete a note
@views.route('/delete-note', methods=['POST'])
def delete_task():  
    note = json.loads(request.data)  # This function expects JSON data
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


# Route to add a task
@views.route('/add', methods=['GET', 'POST'])
@login_required
def task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')

        if not title or not date:
            flash("Title and date are required!", category='error')
        else:
            try:
                task_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                new_task = Task(
                    title=title,
                    description=description,
                    date=task_date,
                    user_id=current_user.id
                )

                db.session.add(new_task)
                db.session.commit()
                flash('Task added successfully!', category='success')
                return redirect(url_for('views.home'))
            except ValueError:
                flash('Invalid date format!', category='error')

    return render_template('add_task.html', user=current_user)

@views.route('/update-task-status', methods=['POST'])
@login_required
def update_task_status():
    data = json.loads(request.data)
    task_id = data.get('taskId')
    is_done = data.get('isDone')

    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        task.is_done = is_done
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Unauthorized or invalid task'}), 403

# notifications 
import smtplib
from email.mime.text import MIMEText
import datetime

class Task:
    def __init__(self, id, name, deadline, completed=False):
        self.id = id
        self.name = name
        self.deadline = deadline
        self.completed = completed

class Calendar:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def get_tasks(self):
        return self.tasks

def sen_email(subject, body, to_email):
    from_email = "example@gmail.com"
    password = "password"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp@gmail.com", 465) as server:
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())

def notify_user(task, message):
    subject = f"Task Notification: {task.name}"
    body = message
    to_email = "user_email@example.com"
    send_email(subject, body, to_email)

def check_notifications(calendar):
    now = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)

    for task in calendar.get_task():
        if task.completed:
            notify_user(task,f"The task {task.name} has  been completed. Goodjob, keep it up!")
        elif now > task.deadline:
            notify_user(task, f"The deadline for the task {task.name} has been passed. Make sure to update your task list.")
        elif now + one_day > task.deadline > now:
            notify_user(task, f"The deadline for the task {task.name} is tomorrow. Don't forget to accomplished it. You can do it, goodluck!")