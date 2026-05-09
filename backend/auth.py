from flask import Blueprint, request, jsonify
from backend.models import db, User, Role
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

JWT_SECRET = os.getenv('JWT_SECRET')

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except:
        return None

@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'All fields required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        role=Role.ADMIN.value if email == 'admin@test.com' else Role.MEMBER.value  # quick admin for testing
    )
    db.session.add(new_user)
    db.session.commit()

    token = generate_token(new_user.id, new_user.role)
    return jsonify({
        'message': 'User created',
        'token': token,
        'user': {'id': new_user.id, 'name': new_user.name, 'email': new_user.email, 'role': new_user.role}
    }), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user.id, user.role)
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}
    }), 200