
from flask import Blueprint, render_template, jsonify
from ..models.service import Service, ServiceRequest, Review
from ..models.user import User
from sqlalchemy import func
from .. import db 

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    total_services = Service.query.count()
    total_professionals = User.query.filter_by(role='professional', is_active=True).count()
    total_customers = User.query.filter_by(role='customer').count()
    completed_services = ServiceRequest.query.filter_by(status='closed').count()
    featured_services = db.session.query(
        Service,
        db.func.count(ServiceRequest.id).label('request_count')
    ).join(ServiceRequest, Service.id == ServiceRequest.service_id)\
    .group_by(Service.id)\
    .order_by(db.func.count(ServiceRequest.id).desc())\
    .limit(6).all()
    
    top_professionals = db.session.query(
        User,
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('review_count')
    ).join(Review, User.id == Review.professional_id)\
    .filter(User.role == 'professional', User.is_active == True)\
    .group_by(User.id)\
    .having(func.count(Review.id) >= 5)\
    .order_by(func.avg(Review.rating).desc())\
    .limit(4).all()
    
    return render_template('index.html',
                         total_services=total_services,
                         total_professionals=total_professionals,
                         total_customers=total_customers,
                         completed_services=completed_services,
                         featured_services=featured_services,
                         top_professionals=top_professionals)

@bp.route('/services/list')
def list_services():
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': service.id,
        'name': service.name,
        'base_price': service.base_price,
        'time_required': service.time_required,
        'description': service.description
    } for service in services])

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500