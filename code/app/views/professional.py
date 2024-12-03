
from flask import Blueprint, render_template, redirect, url_for, flash, request,jsonify
from flask_login import login_required, current_user
from ..models.service import ServiceRequest, Review, LocationUpdate
from .. import db
from datetime import datetime
from ..utils.decorators import professional_required
from functools import wraps
from datetime import timedelta
from ..models.service import RejectionReason

bp = Blueprint('professional', __name__, url_prefix='/professional')

def professional_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'professional':
            flash('You need to be a service professional to access this page.')
            return redirect(url_for('main.index'))
        if not current_user.is_active:
            flash('Your account is pending approval or has been deactivated.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@professional_required
def dashboard():
    total_requests = ServiceRequest.query.filter_by(professional_id=current_user.id).count()
    active_requests = ServiceRequest.query.filter_by(
        professional_id=current_user.id,
        status='assigned'
    ).count()
    completed_requests = ServiceRequest.query.filter_by(
        professional_id=current_user.id,
        status='closed'
    ).count()
    
    reviews = Review.query.filter_by(professional_id=current_user.id).all()
    avg_rating = sum(review.rating for review in reviews) / len(reviews) if reviews else 0
    recent_reviews = Review.query.filter_by(professional_id=current_user.id)\
        .order_by(Review.date_created.desc()).limit(5).all()
    
    return render_template('professional/dashboard.html',
                         total_requests=total_requests,
                         active_requests=active_requests,
                         completed_requests=completed_requests,
                         avg_rating=avg_rating,
                         recent_reviews=recent_reviews)

@bp.route('/requests')
@login_required
@professional_required
def manage_requests():
    status = request.args.get('status', 'available')
    
    if status == 'available':
        requests = ServiceRequest.query.filter_by(
            status='requested',
            service_id=current_user.service_type_id
        ).order_by(ServiceRequest.date_of_request.desc()).all()
    elif status == 'assigned':
        requests = ServiceRequest.query.filter_by(
            professional_id=current_user.id,
            status='assigned'
        ).order_by(ServiceRequest.date_of_request.desc()).all()
    elif status == 'completed':
        requests = ServiceRequest.query.filter_by(
            professional_id=current_user.id,
            status='closed' 
        ).order_by(ServiceRequest.date_of_request.desc()).all()
    
    return render_template('professional/manage_requests.html',
                         requests=requests,
                         current_status=status)

@bp.route('/request/<int:request_id>/accept', methods=['POST'])
@login_required
@professional_required
def accept_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.status != 'requested':
        flash('This request is no longer available.')
        return redirect(url_for('professional.manage_requests'))
    
    if service_request.service_id != current_user.service_type_id:
        flash('You can only accept requests matching your service type.')
        return redirect(url_for('professional.manage_requests'))
    
    try:
        service_request.professional_id = current_user.id
        service_request.status = 'assigned'
        db.session.commit()
        flash('Service request accepted successfully!')
    except:
        db.session.rollback()
        flash('Error accepting request. Please try again.')
    
    return redirect(url_for('professional.manage_requests'))

@bp.route('/request/<int:request_id>/complete', methods=['POST'])
@login_required
@professional_required
def complete_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.professional_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('professional.manage_requests'))
    
    if service_request.status != 'assigned':
        flash('Can only complete assigned requests', 'error')
        return redirect(url_for('professional.manage_requests'))
    
    try:
        service_request.status = 'closed'  
        service_request.date_of_completion = datetime.utcnow()
        db.session.commit()
        flash('Service request marked as completed!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing request: {str(e)}', 'error')
    
    return redirect(url_for('professional.manage_requests', status='completed'))

@bp.route('/request/<int:request_id>/reject', methods=['POST'])
@login_required
@professional_required
def reject_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.status not in ['requested', 'assigned']:
        flash('This request is no longer available for rejection.', 'error')
        return redirect(url_for('professional.manage_requests'))
    
    try:
        reason = request.form.get('reason', 'No reason provided')
        rejection = RejectionReason(
            service_request_id=request_id,
            professional_id=current_user.id,
            reason=reason
        )
        db.session.add(rejection)
        service_request.status = 'rejected'
        db.session.commit()
        
        flash('Service request rejected successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting request: {str(e)}', 'error')
    
    return redirect(url_for('professional.manage_requests'))

@bp.route('/reviews')
@login_required
@professional_required
def view_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = 10 
    
    reviews = Review.query.filter_by(professional_id=current_user.id)\
        .order_by(Review.date_created.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    total_reviews = Review.query.filter_by(professional_id=current_user.id).count()
    if total_reviews > 0:
        avg_rating = db.session.query(db.func.avg(Review.rating))\
            .filter_by(professional_id=current_user.id).scalar() or 0
        rating_counts = db.session.query(Review.rating, db.func.count(Review.id))\
            .filter_by(professional_id=current_user.id)\
            .group_by(Review.rating).all()
        rating_counts = dict(rating_counts)
    else:
        avg_rating = 0
        rating_counts = {i: 0 for i in range(1, 6)}
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_reviews = Review.query.filter_by(professional_id=current_user.id)\
        .filter(Review.date_created >= thirty_days_ago).all()
    recent_rating = sum(r.rating for r in recent_reviews) / len(recent_reviews) if recent_reviews else 0
    total_requests = ServiceRequest.query.filter_by(professional_id=current_user.id).count()
    completed_requests = ServiceRequest.query.filter_by(
        professional_id=current_user.id,
        status='closed'
    ).count()
    completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    return render_template('professional/reviews.html',
                         reviews=reviews,
                         total_reviews=total_reviews,
                         avg_rating=avg_rating,
                         rating_counts=rating_counts,
                         recent_rating=recent_rating,
                         completion_rate=completion_rate)


@bp.route('/service/<int:request_id>/location', methods=['POST'])
@login_required
@professional_required
def update_location(request_id):
    request = ServiceRequest.query.get_or_404(request_id)
    data = request.get_json()
    
    location_update = LocationUpdate(
        service_request_id=request_id,
        latitude=data['latitude'],
        longitude=data['longitude'],
        update_type=data['type']
    )
    
    if data['type'] == 'exited':
        request.service_ended_at = datetime.utcnow()
        request.status = 'completed'
    
    db.session.add(location_update)
    db.session.commit()
    return jsonify({'status': 'success'})

