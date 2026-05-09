from flask import Blueprint, request, jsonify
from backend.models import db, Project, ProjectMember, User
from backend.auth import decode_token
from functools import wraps

projects_bp = Blueprint('projects', __name__)

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

@projects_bp.route('/api/projects', methods=['POST'])
@require_auth
def create_project():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Project name required'}), 400

    project = Project(
        name=name,
        description=description,
        owner_id=request.current_user['id']
    )
    db.session.add(project)
    db.session.commit()

    # Auto add owner as member
    member = ProjectMember(project_id=project.id, user_id=request.current_user['id'])
    db.session.add(member)
    db.session.commit()

    return jsonify({'id': project.id, 'name': project.name, 'description': project.description}), 201

@projects_bp.route('/api/projects', methods=['GET'])
@require_auth
def get_projects():
    projects = Project.query.filter(
        (Project.owner_id == request.current_user['id']) |
        (Project.id.in_([m.project_id for m in ProjectMember.query.filter_by(user_id=request.current_user['id']).all()]))
    ).all()

    result = [{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'owner_id': p.owner_id
    } for p in projects]
    return jsonify(result)