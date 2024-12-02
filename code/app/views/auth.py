
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from ..models.user import User
from ..models.service import Service
from ..models.documents import ProfessionalDocument
from .. import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email
import os
from datetime import datetime
from werkzeug.utils import secure_filename

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        # For professionals, check if they're approved
        if user.role == 'professional' and not user.is_active:
            flash('Your account is pending approval or has been deactivated. Please contact admin.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember.data)
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.role == 'admin':
                next_page = url_for('admin.dashboard')
            elif user.role == 'professional':
                next_page = url_for('professional.dashboard')
            else:
                next_page = url_for('customer.dashboard')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)
    
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/register/<role>', methods=['GET', 'POST'])
def register(role):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if role not in ['customer', 'professional']:
        return redirect(url_for('main.index'))
    
    # Get all services for professional registration
    services = []
    if role == 'professional':
        services = Service.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            role=role,
            location=request.form['location'],
            pin_code=request.form['pin_code']
        )
        user.set_password(request.form['password'])
        
        if role == 'professional':
            user.service_type_id = request.form.get('service_type')
            user.experience = request.form.get('experience')
            user.description = request.form.get('description')
            user.is_active = False  # Requires admin approval
            
        try:
            db.session.add(user)
            db.session.commit()
            
            # Handle document upload for professionals
            if role == 'professional' and 'documents' in request.files:
                files = request.files.getlist('documents')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # Create unique filename with timestamp
                        base, ext = os.path.splitext(filename)
                        unique_filename = f"{base}_{user.id}_{int(datetime.utcnow().timestamp())}{ext}"
                        
                        # Create upload directory if it doesn't exist
                        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(upload_dir, unique_filename)
                        file.save(file_path)
                        
                        # Create document record
                        document = ProfessionalDocument(
                            professional_id=user.id,
                            document_type='Identity/Certification',
                            file_name=filename,
                            file_path=file_path
                        )
                        db.session.add(document)
                
                db.session.commit()
            
            flash('Registration successful!')
            if role == 'professional':
                flash('Please wait for admin approval before logging in.')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed. Please try again. Error: {str(e)}')
    
    return render_template('auth/register.html', role=role, services=services)
@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
    