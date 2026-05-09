from flask import Blueprint, request, jsonify
from backend.models import db, Task, Project, ProjectMember
from backend.auth import decode_token
from functools import wraps
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        token = token.split('Bearer ')[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        request.current_user = {'id': payload['user_id'], 'role': payload['role']}
        return f(*args, **kwargs)
    return decorated

# Simple helper to check if user can access project
def can_access_project(user_id, project_id):
    project = Project.query.get(project_id)
    if not project:
        return False
    if project.owner_id == user_id:
        return True
    return ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first() is not None

@tasks_bp.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@require_auth
def create_task(project_id):
    if not can_access_project(request.current_user['id'], project_id):
        return jsonify({'error': 'No access to this project'}), 403

    data = request.get_json()
    task = Task(
        title=data.get('title'),
        description=data.get('description'),
        project_id=project_id,
        assignee_id=data.get('assignee_id'),
        created_by_id=request.current_user['id'],
        due_date=datetime.fromisoformat(data.get('due_date')) if data.get('due_date') else None
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'id': task.id, 'title': task.title, 'status': task.status}), 201

@tasks_bp.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
@require_auth
def get_tasks(project_id):
    if not can_access_project(request.current_user['id'], project_id):
        return jsonify({'error': 'No access to this project'}), 403

    tasks = Task.query.filter_by(project_id=project_id).all()
    result = [{
        'id': t.id,
        'title': t.title,
        'status': t.status,
        'priority': t.priority,
        'due_date': t.due_date.isoformat() if t.due_date else None,
        'assignee_id': t.assignee_id
    } for t in tasks]
    return jsonify(result)
