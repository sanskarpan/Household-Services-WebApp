
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, send_file, current_app
from flask_login import login_required, current_user
from ..models.service import Service, ServiceRequest
from ..models.user import User
from ..utils.decorators import admin_required
from..utils.helpers import allowed_file
from .. import db
import os
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from ..models.service import Review
from ..utils.helpers import generate_csv_report,generate_pdf_report
from ..models.documents import ProfessionalDocument

bp = Blueprint('admin', __name__, url_prefix='/admin')

#for DUMMY data
# @bp.route('/dashboard')
# @login_required
# @admin_required
# def dashboard():
#     # Get overall statistics
#     stats = {
#         'total_customers': 25,  # Dummy data
#         'total_professionals': 10,  # Dummy data
#         'active_requests': 7,  # Dummy data
#         'completed_requests': 15  # Dummy data
#     }
    
#     # Dummy data for recent activities
#     recent_registrations = []
#     recent_requests = []
#     pending_approvals = []

#     # Dummy data for charts
#     today = datetime.now().date()
#     last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
#     dates = [date.strftime('%Y-%m-%d') for date in last_7_days]
#     request_counts = [5, 8, 2, 4, 7, 1, 6]  # Dummy values for requests over the last 7 days

#     service_names = ['Cleaning', 'Plumbing', 'Electrical', 'Gardening']  # Dummy service names
#     service_revenue = [1200, 800, 950, 500]  # Dummy revenue values

#     growth_dates = ['01', '02', '03', '04', '05', '06']  # Last 6 months
#     customer_growth = [3, 5, 7, 10, 12, 15]  # Dummy values for customers
#     professional_growth = [1, 2, 2, 3, 4, 5]  # Dummy values for professionals

#     return render_template(
#         'admin/dashboard.html',
#         stats=stats,
#         recent_registrations=recent_registrations,
#         recent_requests=recent_requests,
#         pending_approvals=pending_approvals,
#         revenue=sum(service_revenue),  # Total revenue
#         dates=dates,
#         request_counts=request_counts,
#         service_names=service_names,
#         service_revenue=service_revenue,
#         growth_dates=growth_dates,
#         customer_growth=customer_growth,
#         professional_growth=professional_growth
#     )


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get overall statistics
    stats = {
        'total_customers': User.query.filter_by(role='customer').count(),
        'total_professionals': User.query.filter_by(role='professional').count(),
        'active_requests': ServiceRequest.query.filter(
            ServiceRequest.status.in_(['requested', 'assigned'])
        ).count(),
        'completed_requests': ServiceRequest.query.filter_by(status='closed').count()
    }
    
    # Get recent activities
    recent_registrations = User.query.order_by(User.date_created.desc()).limit(5).all()
    recent_requests = ServiceRequest.query.order_by(ServiceRequest.date_of_request.desc()).limit(5).all()
    pending_approvals = User.query.filter_by(
        role='professional',
        is_active=False
    ).order_by(User.date_created.desc()).all()
    
    # Revenue statistics
    today = datetime.now().date()
    month_start = today.replace(day=1)
    revenue_stats = db.session.query(
        func.sum(Service.base_price)
    ).join(ServiceRequest).filter(
        ServiceRequest.status == 'closed',
        ServiceRequest.date_of_completion >= month_start
    ).scalar() or 0

    # Data for Service Requests Chart (Last 7 Days)
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    dates = [date.strftime('%Y-%m-%d') for date in last_7_days]
    request_counts = [
        ServiceRequest.query.filter(
            func.date(ServiceRequest.date_of_request) == date
        ).count()
        for date in last_7_days
    ]

    # Data for Revenue by Service Chart
    revenue_by_service = db.session.query(
        Service.name,
        func.sum(Service.base_price)
    ).join(ServiceRequest).filter(
        ServiceRequest.status == 'closed',
        ServiceRequest.date_of_completion >= month_start
    ).group_by(Service.name).all()
    service_names = [entry[0] for entry in revenue_by_service]
    service_revenue = [entry[1] for entry in revenue_by_service]

    # Data for User Growth Chart (Last 6 Months)
    six_months_ago = month_start - timedelta(days=30*6)
    user_growth_query = db.session.query(
        extract('month', User.date_created).label('month'),
        func.count().label('count'),
        User.role
    ).filter(
        User.date_created >= six_months_ago
    ).group_by('month', User.role).all()
    growth_dates = [f'{int(entry[0]):02d}' for entry in user_growth_query]
    customer_growth = [entry[1] for entry in user_growth_query if entry[2] == 'customer']
    professional_growth = [entry[1] for entry in user_growth_query if entry[2] == 'professional']

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_registrations=recent_registrations,
        recent_requests=recent_requests,
        pending_approvals=pending_approvals,
        revenue=revenue_stats,
        # Chart data
        dates=dates,
        request_counts=request_counts,
        service_names=service_names,
        service_revenue=service_revenue,
        growth_dates=growth_dates,
        customer_growth=customer_growth,
        professional_growth=professional_growth
    )


@bp.route('/services')
@login_required
@admin_required
def manage_services():
    services = Service.query.all()
    return render_template('admin/manage_services.html', services=services)

@bp.route('/services/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    if request.method == 'POST':
        service = Service(
            name=request.form['name'],
            description=request.form['description'],
            base_price=float(request.form['base_price']),
            time_required=int(request.form['time_required'])
        )
        
        try:
            db.session.add(service)
            db.session.commit()
            flash('Service added successfully!')
            return redirect(url_for('admin.manage_services'))
        except:
            db.session.rollback()
            flash('Error adding service. Please try again.', 'error')
    
    return render_template('admin/service_requests.html')

@bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(id):  
    service = Service.query.get_or_404(id)
    
    if request.method == 'POST':
        service.name = request.form['name']
        service.base_price = float(request.form['base_price'])
        service.time_required = int(request.form['time_required'])
        service.description = request.form['description']
        service.is_active = 'is_active' in request.form
        
        try:
            db.session.commit()
            flash('Service updated successfully!')
            return redirect(url_for('admin.manage_services'))
        except:
            db.session.rollback()
            flash('Error updating service. Please try again.')
    
    return render_template('admin/service_requests.html', service=service)

@bp.route('/users')
@login_required
@admin_required
def manage_users():
    role = request.args.get('role', 'professional')
    status = request.args.get('status')
    search = request.args.get('search', '')
    
    query = User.query.filter_by(role=role)
    
    if status:
        if status == 'pending':
            query = query.filter_by(is_active=False)
        elif status == 'active':
            query = query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.date_created.desc()).all()
    services = Service.query.all()
    
    return render_template('admin/manage_users.html',
                         users=users,
                         current_role=role,
                         current_status=status,
                         services=services)

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_users', role=user.role))

@bp.route('/professionals/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_professional(user_id):
    professional = User.query.get_or_404(user_id)
    
    if professional.role != 'professional':
        abort(400)
    
    professional.is_active = True
    
    try:
        db.session.commit()
        flash('Professional approved successfully!')
    except:
        db.session.rollback()
        flash('Error approving professional. Please try again.', 'error')
    
    return redirect(url_for('admin.manage_users', role='professional'))

@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    service_stats = db.session.query(
        Service.name,
        func.count(ServiceRequest.id).label('request_count'),
        func.avg(Service.base_price).label('avg_price')
    ).outerjoin(ServiceRequest).group_by(Service.id).all()
    
    pro_stats = db.session.query(
        User,
        func.count(ServiceRequest.id).label('request_count'),
        func.avg(Review.rating).label('avg_rating')
    ).filter(User.role == 'professional')\
    .outerjoin(ServiceRequest, User.id == ServiceRequest.professional_id)\
    .outerjoin(Review, ServiceRequest.id == Review.service_request_id)\
    .group_by(User.id).all()
    
    revenue_data = db.session.query(
        func.date(ServiceRequest.date_of_completion).label('date'),
        func.sum(Service.base_price).label('revenue')
    ).join(Service)\
    .filter(
        ServiceRequest.status == 'closed',
        ServiceRequest.date_of_completion.between(start_date, end_date)
    ).group_by('date').all()
    
    return render_template('admin/analytics.html',
                         service_stats=service_stats,
                         pro_stats=pro_stats,
                         revenue_data=revenue_data)

@bp.route('/reports/export')
@login_required
@admin_required
def export_reports():
    report_type = request.args.get('type', 'services')
    format_type = request.args.get('format', 'csv')
    
    if report_type == 'services':
        data = Service.query.all()
    elif report_type == 'professionals':
        data = User.query.filter_by(role='professional').all()
    elif report_type == 'requests':
        data = ServiceRequest.query.all()
    else:
        abort(400)
    
    if format_type == 'csv':
        return generate_csv_report(data, report_type)
    elif format_type == 'pdf':
        return generate_pdf_report(data, report_type)
    else:
        abort(400)


@bp.route('/api/v1/professional/<int:user_id>/documents')
@login_required
@admin_required
def get_professional_documents(user_id):
    try:
        documents = ProfessionalDocument.query.filter_by(professional_id=user_id).all()
        
        if not documents:
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    if allowed_file(filename):
                        file_path = os.path.join(upload_dir, filename)
                        doc = ProfessionalDocument(
                            professional_id=user_id,
                            document_type='Identity/Certification',
                            file_name=filename,
                            file_path=file_path
                        )
                        db.session.add(doc)
                
                db.session.commit()
                documents = ProfessionalDocument.query.filter_by(professional_id=user_id).all()
        
        return jsonify({
            'documents': [{
                'id': doc.id,
                'document_type': doc.document_type,
                'file_name': doc.file_name,
                'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'verified': doc.verified,
                'verification_note': doc.verification_note,
                'file_path': url_for('admin.view_document', document_id=doc.id)
            } for doc in documents]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/document/<int:document_id>')
@login_required
@admin_required
def view_document(document_id):
    document = ProfessionalDocument.query.get_or_404(document_id)
    if not current_user.role == 'admin':
        abort(403)
    try:
        return send_file(
            document.file_path,
            as_attachment=False,
            download_name=document.file_name
        )
    except FileNotFoundError:
        abort(404)


@bp.route('/document/<int:document_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_document(document_id):
    document = ProfessionalDocument.query.get_or_404(document_id)
    
    try:
        verified = request.form.get('verified') == 'true'
        note = request.form.get('note', '')
        document.verified = verified
        document.verification_note = note
        document.verified_at = datetime.utcnow() if verified else None
        document.verified_by = current_user.id if verified else None
        if verified:
            professional = User.query.get(document.professional_id)
            if professional and not professional.is_active:
                all_docs_verified = all(doc.verified for doc in professional.documents)
                if all_docs_verified:
                    professional.is_active = True
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Document verification status updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error verifying document: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
@bp.route('/users/<int:user_id>/block', methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason')
    
    user.is_blocked = True
    user.block_reason = reason
    user.blocked_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'User {user.username} has been blocked.', 'success')
    return redirect(url_for('admin.manage_users', role=user.role))


@bp.route('/users/<int:user_id>/warn', methods=['POST'])
@login_required
@admin_required
def warn_user(user_id):
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason')
    
    user.warning_count += 1
    user.last_warning_at = datetime.utcnow()
    if user.warning_count >= 3:  
        user.is_blocked = True
        user.block_reason = f"Automatically blocked after {user.warning_count} warnings"
        user.blocked_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Warning issued to {user.username}', 'warning')
    return redirect(url_for('admin.manage_users', role=user.role))  

