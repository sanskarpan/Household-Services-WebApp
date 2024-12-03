
from flask_restx import Resource
from ..api.models import login_model, register_model
from ..api import auth_ns
from..utils.helpers import create_token
from ..models.user import User
from .. import db

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.doc('user_login')
    def post(self):
        data = auth_ns.payload
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            return {
                'token': create_token(user),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            }
        return {'message': 'Invalid credentials'}, 401

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.doc('user_register')
    def post(self):
        """User registration endpoint"""
        data = auth_ns.payload
        
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already registered'}, 400
            
        user = User(
            username=data['username'],
            email=data['email'],
            role=data['role'],
            location=data['location'],
            pin_code=data['pin_code']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return {'message': 'Registration successful'}, 201