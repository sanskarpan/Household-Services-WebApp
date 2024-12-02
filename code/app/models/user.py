
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .. import db, login_manager
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'professional', 'customer'
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.Text)
    blocked_at = db.Column(db.DateTime)
    warning_count = db.Column(db.Integer, default=0)
    last_warning_at = db.Column(db.DateTime)
    
    # Role-specific fields
    description = db.Column(db.Text)  # For professionals
    service_type_id = db.Column(db.Integer, db.ForeignKey('services.id'))  # For professionals
    experience = db.Column(db.Integer)  # For professionals
    location = db.Column(db.String(100))
    pin_code = db.Column(db.String(10))
    
    # Relationships
    service_requests_customer = db.relationship('ServiceRequest', 
                                              backref='customer',
                                              foreign_keys='ServiceRequest.customer_id')
    service_requests_professional = db.relationship('ServiceRequest', 
                                                  backref='professional',
                                                  foreign_keys='ServiceRequest.professional_id')
    reviews_given = db.relationship('Review', 
                                  foreign_keys='Review.customer_id',
                                  backref='customer')
    reviews_received = db.relationship('Review', 
                                     foreign_keys='Review.professional_id',
                                     backref='professional')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

