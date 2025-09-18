from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Change this in production!
app.permanent_session_lifetime = timedelta(days=7)

# CORS setup
CORS(app, supports_credentials=True)

# SQLite database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------ #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    due_date = db.Column(db.String(20))
    status = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ------------------ ROUTES ------------------ #
@app.route('/')
def home():
    return jsonify({'message': 'API is working!'})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid email or password'}), 401

    session.permanent = True
    session['user_id'] = user.id
    return jsonify({'message': 'Login successful'}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'}), 200

@app.route('/user')
def get_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    return jsonify({'id': user.id, 'email': user.email})

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    if request.method == 'POST':
        data = request.get_json()
        task = Task(
            title=data.get('title'),
            due_date=data.get('dueDate', ''),
            status=data.get('status', 'todo'),
            user_id=user_id
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({'message': 'Task added'}), 201

    else:
        task_list = Task.query.filter_by(user_id=user_id).all()
        return jsonify([{
            'id': t.id,
            'title': t.title,
            'dueDate': t.due_date,
            'status': t.status
        } for t in task_list])

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
