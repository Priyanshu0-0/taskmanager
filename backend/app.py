from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from enum import Enum
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from flask import Flask, send_from_directory

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..'), filename)

@app.route('/')
def home():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..'), 'indexing.html')

load_dotenv()

app = Flask(__name__)
CORS(app)

db_url = os.getenv('DATABASE_URL', 'sqlite:///taskmanager.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+pg8000://', 1)
elif db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'supersecretkeychangethisinproduction123456789012345')

db = SQLAlchemy(app)

# ===================== MODELS =====================
class Role(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default=Role.MEMBER.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default=TaskStatus.TODO.value)
    priority = db.Column(db.String(20), default=Priority.MEDIUM.value)
    due_date = db.Column(db.DateTime, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===================== AUTH =====================
JWT_SECRET = os.getenv('JWT_SECRET', 'supersecretkeychangethisinproduction123456789012345')

def generate_token(user_id, role):
    payload = {'user_id': user_id, 'role': role, 'exp': datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except:
        return None

def require_auth(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Missing token'}), 401
        payload = decode_token(token.split('Bearer ')[1].strip())
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        request.current_user = {'id': payload['user_id'], 'role': payload['role']}
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# ===================== LOGIN / SIGNUP =====================
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'All fields required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    role = Role.ADMIN.value if email == 'admin@test.com' else Role.MEMBER.value

    new_user = User(name=name, email=email, password_hash=password_hash, role=role)
    db.session.add(new_user)
    db.session.commit()

    token = generate_token(new_user.id, new_user.role)
    return jsonify({'message': 'User created', 'token': token, 'role': new_user.role}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = generate_token(user.id, user.role)
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}
    }), 200

# ===================== PROJECTS =====================
@app.route('/api/projects', methods=['POST'])
@require_auth
def create_project():
    data = request.get_json()
    project = Project(name=data.get('name'), description=data.get('description'), owner_id=request.current_user['id'])
    db.session.add(project)
    db.session.commit()

    db.session.add(ProjectMember(project_id=project.id, user_id=request.current_user['id']))
    db.session.commit()

    return jsonify({'id': project.id, 'name': project.name, 'description': project.description}), 201

@app.route('/api/projects', methods=['GET'])
@require_auth
def get_projects():
    if request.current_user['role'] == 'ADMIN':
        projects = Project.query.all()
    else:
        projects = Project.query.filter(
            (Project.owner_id == request.current_user['id']) |
            (Project.id.in_([m.project_id for m in ProjectMember.query.filter_by(user_id=request.current_user['id']).all()]))
        ).all()
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description} for p in projects])

@app.route('/api/projects/<int:project_id>/members', methods=['POST'])
@require_auth
def add_member(project_id):
    if request.current_user['role'] != 'ADMIN':
        project = Project.query.get(project_id)
        if not project or project.owner_id != request.current_user['id']:
            return jsonify({'error': 'Not authorized'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    member = ProjectMember(project_id=project_id, user_id=user_id)
    db.session.add(member)
    db.session.commit()
    return jsonify({'message': 'Member added'}), 201

# ===================== TASKS =====================
@app.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@require_auth
def create_task(project_id):
    data = request.get_json()
    task = Task(
        title=data.get('title'),
        description=data.get('description'),
        project_id=project_id,
        assignee_id=data.get('assignee_id'),
        created_by_id=request.current_user['id'],
        status=data.get('status', 'TODO'),
        priority=data.get('priority', 'MEDIUM')
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'id': task.id, 'title': task.title}), 201

@app.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
@require_auth
def get_tasks(project_id):
    tasks = Task.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'id': t.id, 'title': t.title, 'status': t.status,
        'priority': t.priority, 'assignee_id': t.assignee_id
    } for t in tasks])
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Allow delete if admin or task creator
    if request.current_user['role'] == 'ADMIN' or task.created_by_id == request.current_user['id']:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    else:
        return jsonify({'error': 'Not authorized to delete this task'}), 403

# ===================== STARTUP =====================
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return {"message": "Task Manager API is running"}

if __name__ == '__main__':
    app.run(debug=True)