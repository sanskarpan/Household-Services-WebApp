
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models.service import Service, ServiceRequest, Review
from functools import wraps
from ..models.user import User
from .. import db
from datetime import datetime
from sqlalchemy import or_

bp = Blueprint('customer', __name__, url_prefix='/customer')

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'customer':
            flash('You need to be a customer to access this page.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@customer_required
def dashboard():
    active_requests = ServiceRequest.query.filter_by(
        customer_id=current_user.id
    ).filter(
        ServiceRequest.status.in_(['requested', 'assigned']) 
    ).order_by(ServiceRequest.date_of_request.desc()).all()
    
    past_requests = ServiceRequest.query.filter_by(
        customer_id=current_user.id
    ).filter(
        ServiceRequest.status.in_(['closed', 'cancelled', 'rejected'])  
    ).order_by(ServiceRequest.date_of_completion.desc()).all()
    
    return render_template('customer/dashboard.html',
                         active_requests=active_requests,
                         past_requests=past_requests)

@bp.route('/services/search')
@login_required
@customer_required
def search_services():
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    pin_code = request.args.get('pin_code', '')
    services = Service.query.filter_by(is_active=True)
    if query:
        services = services.filter(
            db.or_(
                Service.name.ilike(f'%{query}%'),
                Service.description.ilike(f'%{query}%')
            )
        )
    
    services = services.all()
    service_professionals = {}
    for service in services:
        professionals = User.query.filter_by(
            role='professional',
            is_active=True,
            service_type_id=service.id
        )
        
        if location or pin_code:
            if pin_code:
                professionals = professionals.filter_by(pin_code=pin_code)
            if location:
                professionals = professionals.filter(User.location.ilike(f'%{location}%'))
        
        service_professionals[service.id] = professionals.all()
    
    return render_template('customer/search_services.html',
                         services=services,
                         service_professionals=service_professionals,
                         query=query,
                         location=location,
                         pin_code=pin_code)

@bp.route('/service-request/create/<int:service_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def create_service_request(service_id):
    service = Service.query.get_or_404(service_id)
    professionals = User.query.filter_by(
        role='professional',
        is_active=True,
        service_type_id=service_id
    ).all()
    if request.method == 'POST':
        service_request = ServiceRequest(
            service_id=service_id,
            customer_id=current_user.id,
            preferred_date=datetime.strptime(request.form['preferred_date'], '%Y-%m-%d'),
            location=request.form['location'],
            pin_code=request.form['pin_code'],
            remarks=request.form['remarks']
        )
        
        professional_id = request.form.get('professional_id')
        if professional_id:
            service_request.professional_id = professional_id
            service_request.status = 'assigned'
        
        try:
            db.session.add(service_request)
            db.session.commit()
            flash('Service request created successfully!')
            return redirect(url_for('customer.dashboard'))
        except:
            db.session.rollback()
            flash('Error creating service request. Please try again.')
    
    professionals = User.query.filter_by(
        role='professional',
        is_active=True,
        service_type_id=service_id
    ).all()
    
    return render_template('customer/service_request.html',
                         service=service,
                         professionals=professionals)

@bp.route('/service-request/<int:request_id>/cancel', methods=['POST'])
@login_required
@customer_required
def cancel_service_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.customer_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('customer.dashboard'))
    
    if service_request.status == 'closed':
        flash('Cannot cancel a closed service request.', 'error')
        return redirect(url_for('customer.dashboard'))
    
    if service_request.status not in ['requested', 'assigned']:
        flash('This request cannot be cancelled.', 'error')
        return redirect(url_for('customer.dashboard'))
    
    try:

        if service_request.status == 'assigned':
           
            service_request.status = 'cancelled'
            flash('Service request cancelled. The professional has been notified.', 'success')
        else:
            service_request.status = 'cancelled'
            flash('Service request cancelled successfully.', 'success')
        
        db.session.commit()
    except:
        db.session.rollback()
        flash('Error cancelling service request. Please try again.', 'error')
    

    
    return redirect(url_for('customer.dashboard'))

@bp.route('/service-request/<int:request_id>/review', methods=['GET', 'POST'])
@login_required
@customer_required
def review_service(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.customer_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('customer.dashboard'))
    
    if service_request.status != 'closed':
        flash('Can only review completed services', 'error')
        return redirect(url_for('customer.dashboard'))
    
    if service_request.review:
        flash('You have already reviewed this service', 'warning')
        return redirect(url_for('customer.dashboard'))
    
    if request.method == 'POST':
        try:
            review = Review(
                service_request_id=request_id,
                customer_id=current_user.id,
                professional_id=service_request.professional_id,
                rating=int(request.form['rating']),
                comment=request.form['comment']
            )
            db.session.add(review)
            db.session.commit()
            flash('Review submitted successfully!', 'success')
            return redirect(url_for('customer.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting review: {str(e)}', 'error')
    
    return render_template('customer/review_form.html', service_request=service_request)

