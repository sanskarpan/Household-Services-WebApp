
from flask import current_app, make_response
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import re
import csv
import io
from datetime import datetime
from ..models.service import ServiceRequest
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder):
    if file and allowed_file(file.filename, {'pdf', 'png', 'jpg', 'jpeg'}):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}{ext}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, unique_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        return unique_filename
    return None

def format_phone_number(phone):
    phone = re.sub(r'\D', '', phone)
    if len(phone) == 10:
        return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
    return phone

def format_currency(amount):
    return f"${amount:,.2f}"

def calculate_service_metrics(professional):
    total_services = len(professional.service_requests_professional)
    completed_services = sum(1 for req in professional.service_requests_professional 
                           if req.status == 'closed')
    average_rating = 0
    total_reviews = len(professional.reviews_received)
    
    if total_reviews > 0:
        average_rating = sum(review.rating for review in professional.reviews_received) / total_reviews
    
    completion_rate = (completed_services / total_services * 100) if total_services > 0 else 0
    
    return {
        'total_services': total_services,
        'completed_services': completed_services,
        'average_rating': average_rating,
        'total_reviews': total_reviews,
        'completion_rate': completion_rate
    }

def get_date_range_metrics(start_date, end_date, professional):
    requests = [req for req in professional.service_requests_professional 
               if start_date <= req.date_of_request <= end_date]
    
    total_requests = len(requests)
    completed_requests = sum(1 for req in requests if req.status == 'closed')
    revenue = sum(req.service.base_price for req in requests if req.status == 'closed')
    
    reviews = [review for review in professional.reviews_received 
              if start_date <= review.date_created <= end_date]
    
    avg_rating = sum(review.rating for review in reviews) / len(reviews) if reviews else 0
    
    return {
        'total_requests': total_requests,
        'completed_requests': completed_requests,
        'revenue': revenue,
        'average_rating': avg_rating
    }

def generate_dashboard_data(user):
    if user.role == 'professional':
        return {
            'metrics': calculate_service_metrics(user),
            'recent_requests': user.service_requests_professional[-5:],
            'recent_reviews': user.reviews_received[-5:],
            'monthly_metrics': get_date_range_metrics(
                datetime.now().replace(day=1),
                datetime.now(),
                user
            )
        }
    elif user.role == 'customer':
        return {
            'active_requests': [req for req in user.service_requests_customer 
                              if req.status != 'closed'],
            'completed_requests': [req for req in user.service_requests_customer 
                                 if req.status == 'closed'],
            'total_spent': sum(req.service.base_price for req in user.service_requests_customer 
                             if req.status == 'closed')# app/utils/helpers.py (continued)
        }
    return {}

def validate_pin_code(pin_code):
    return bool(re.match(r'^\d{5,10}$', pin_code))

def validate_password_strength(password):
    """
    Validate password strength
    Must contain at least:
    - 8 characters
    - One uppercase letter
    - One lowercase letter
    - One number
    - One special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
        
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
        
    return True, "Password meets requirements"


def generate_service_report(professional, start_date, end_date):
    """Generate service report for a professional"""
    requests = professional.service_requests_professional.filter(
        ServiceRequest.date_of_request.between(start_date, end_date)
    ).all()
    
    total_revenue = sum(req.service.base_price for req in requests if req.status == 'closed')
    completion_rate = (
        sum(1 for req in requests if req.status == 'closed') / len(requests)
        if requests else 0
    ) * 100
    
    return {
        'total_requests': len(requests),
        'completed_requests': sum(1 for req in requests if req.status == 'closed'),
        'revenue': total_revenue,
        'completion_rate': completion_rate,
        'average_response_time': calculate_average_response_time(requests),
        'customer_satisfaction': calculate_customer_satisfaction(requests)
    }

def calculate_average_response_time(requests):
    """Calculate average response time for service requests"""
    response_times = [
        (req.date_of_assignment - req.date_of_request).total_seconds() / 3600
        for req in requests
        if req.date_of_assignment and req.status != 'requested'
    ]
    return sum(response_times) / len(response_times) if response_times else 0

def calculate_customer_satisfaction(requests):
    """Calculate customer satisfaction score"""
    reviews = [req.review for req in requests if req.review]
    return sum(review.rating for review in reviews) / len(reviews) if reviews else 0

def get_service_availability(professional, date):
    """Check service availability for a professional on a specific date"""
    existing_requests = professional.service_requests_professional.filter(
        ServiceRequest.preferred_date == date,
        ServiceRequest.status.in_(['assigned', 'in_progress'])
    ).count()
    
    max_daily_requests = professional.max_daily_requests or 5
    return max_daily_requests - existing_requests

def format_duration(minutes):
    """Format duration in minutes to human-readable format"""
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minutes"

def generate_csv_report(data, report_type):
    """Generate CSV report based on data type"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'services':
        writer.writerow(['ID', 'Name', 'Base Price', 'Time Required', 'Status', 'Date Created'])
        for service in data:
            writer.writerow([
                service.id,
                service.name,
                service.base_price,
                service.time_required,
                'Active' if service.is_active else 'Inactive',
                service.date_created.strftime('%Y-%m-%d')
            ])
    
    elif report_type == 'professionals':
        writer.writerow(['ID', 'Username', 'Email', 'Service Type', 'Experience', 'Status', 'Join Date'])
        for user in data:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.service_type.name if user.service_type else 'N/A',
                f"{user.experience} years" if user.experience else 'N/A',
                'Active' if user.is_active else 'Inactive',
                user.date_created.strftime('%Y-%m-%d')
            ])
    
    elif report_type == 'requests':
        writer.writerow([
            'ID', 'Service', 'Customer', 'Professional', 'Status',
            'Request Date', 'Completion Date', 'Amount'
        ])
        for request in data:
            writer.writerow([
                request.id,
                request.service.name,
                request.customer.username,
                request.professional.username if request.professional else 'Unassigned',
                request.status.title(),
                request.date_of_request.strftime('%Y-%m-%d'),
                request.date_of_completion.strftime('%Y-%m-%d') if request.date_of_completion else 'N/A',
                request.service.base_price
            ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

def generate_pdf_report(data, report_type):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f"{report_type.title()} Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    if report_type == 'services':
        table_data = [['ID', 'Name', 'Base Price', 'Time Required', 'Status']]
        for service in data:
            table_data.append([
                str(service.id),
                service.name,
                f"${service.base_price:.2f}",
                f"{service.time_required} mins",
                'Active' if service.is_active else 'Inactive'
            ])
    
    elif report_type == 'professionals':
        table_data = [['ID', 'Username', 'Service Type', 'Experience', 'Status']]
        for user in data:
            table_data.append([
                str(user.id),
                user.username,
                user.service_type.name if user.service_type else 'N/A',
                f"{user.experience} years" if user.experience else 'N/A',
                'Active' if user.is_active else 'Inactive'
            ])
    
    elif report_type == 'requests':
        table_data = [['ID', 'Service', 'Customer', 'Status', 'Amount']]
        for request in data:
            table_data.append([
                str(request.id),
                request.service.name,
                request.customer.username,
                request.status.title(),
                f"${request.service.base_price:.2f}"
            ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    elements.append(Spacer(1, 20))
    timestamp = Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles['Normal']
    )
    elements.append(timestamp)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

import jwt
from datetime import datetime, timedelta

def create_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, 'your_secret_key', algorithm='HS256')
    return token