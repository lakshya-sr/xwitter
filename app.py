
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # change this in production!
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.permanent_session_lifetime = timedelta(days=1)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
USER_FILE = 'users.json'

posts = []
post_id_counter = 1

# Load users
if os.path.exists(USER_FILE):
    with open(USER_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_users():
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def index():
    return render_template('index.html', posts=posts, user=session.get('user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return 'Username already exists'
        users[username] = generate_password_hash(password)
        save_users()
        session.permanent = True
        session['user'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_hash = users.get(username)
        if user_hash and check_password_hash(user_hash, password):
            session.permanent = True
            session['user'] = username
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    global post_id_counter
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']
        image_url = None

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(f"{datetime.utcnow().timestamp()}_{image.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                image_url = url_for('static', filename=f'uploads/{filename}')

        post = {
            'id': post_id_counter,
            'user': session['user'],
            'content': content,
            'timestamp': datetime.now(),
            'image': image_url,
            'likes': 0
        }
        post_id_counter += 1
        posts.insert(0, post)
        return redirect(url_for('index'))

    return render_template('create.html', user=session.get('user'))

@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            break
    return redirect(url_for('index'))
if __name__ == "__main__":
    app.run(debug=True)
