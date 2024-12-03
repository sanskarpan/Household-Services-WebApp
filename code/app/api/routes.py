
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from ..models.service import Service, ServiceRequest, Review
from ..models.user import User
from .. import db
from datetime import datetime
from functools import wraps
import jwt
import datetime

bp = Blueprint('api', __name__, url_prefix='/api/v1')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and user.check_password(data.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, current_app.config['SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

@bp.route('/services', methods=['GET'])
def get_services():
    services = Service.query.filter_by(is_active=True).all()
    return jsonify({
        'services': [{
            'id': service.id,
            'name': service.name,
            'base_price': service.base_price,
            'time_required': service.time_required,
            'description': service.description,
        } for service in services]
    })

@bp.route('/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    service = Service.query.get_or_404(service_id)
    professionals = User.query.filter_by(
        role='professional',
        is_active=True,
        service_type_id=service_id
    ).all()
    
    return jsonify({
        'service': {
            'id': service.id,
            'name': service.name,
            'base_price': service.base_price,
            'time_required': service.time_required,
            'description': service.description,
            'professionals': [{
                'id': prof.id,
                'username': prof.username,
                'experience': prof.experience,
                'rating': calculate_rating(prof.id)
            } for prof in professionals]
        }
    })

@bp.route('/service-requests', methods=['GET'])
@token_required
def get_service_requests(current_user):
    if current_user.role == 'customer':
        requests = ServiceRequest.query.filter_by(customer_id=current_user.id).all()
    elif current_user.role == 'professional':
        requests = ServiceRequest.query.filter_by(professional_id=current_user.id).all()
    else:
        requests = ServiceRequest.query.all()
    
    return jsonify({
        'requests': [{
            'id': req.id,
            'service': {
                'id': req.service.id,
                'name': req.service.name
            },
            'customer': req.customer.username,
            'professional': req.professional.username if req.professional else None,
            'status': req.status,
            'preferred_date': req.preferred_date.isoformat(),
            'date_of_request': req.date_of_request.isoformat(),
            'date_of_completion': req.date_of_completion.isoformat() if req.date_of_completion else None
        } for req in requests]
    })

@bp.route('/service-requests', methods=['POST'])
@token_required
def create_service_request(current_user):
    if current_user.role != 'customer':
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    service_request = ServiceRequest(
        service_id=data['service_id'],
        customer_id=current_user.id,
        preferred_date=datetime.datetime.fromisoformat(data['preferred_date']),
        location=data['location'],
        pin_code=data['pin_code'],
        remarks=data.get('remarks')
    )
    
    if data.get('professional_id'):
        service_request.professional_id = data['professional_id']
        service_request.status = 'assigned'
    
    try:
        db.session.add(service_request)
        db.session.commit()
        return jsonify({
            'message': 'Service request created successfully',
            'request_id': service_request.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@bp.route('/reviews/<int:professional_id>', methods=['GET'])
def get_reviews(professional_id):
    reviews = Review.query.filter_by(professional_id=professional_id).all()
    return jsonify({
        'reviews': [{
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'customer': review.customer.username,
            'date': review.date_created.isoformat(),
            'service': review.service_request.service.name
        } for review in reviews]
    })

def calculate_rating(professional_id):
    reviews = Review.query.filter_by(professional_id=professional_id).all()
    if not reviews:
        return 0
    return sum(review.rating for review in reviews) / len(reviews)

