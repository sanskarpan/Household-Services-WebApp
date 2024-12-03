
from .. import db
from datetime import datetime

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.Integer)  
    description = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    professionals = db.relationship('User', backref='service_type')
    service_requests = db.relationship('ServiceRequest', backref='service')
 
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow)
    preferred_date = db.Column(db.DateTime, nullable=False)
    date_of_completion = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='requested')  
    remarks = db.Column(db.Text)
    location = db.Column(db.String(100))
    pin_code = db.Column(db.String(10))
    service_started_at = db.Column(db.DateTime)
    service_ended_at = db.Column(db.DateTime)
    professional_location = db.Column(db.String(255))
    location_updates = db.relationship('LocationUpdate', backref='service_request')
    
    review = db.relationship('Review', backref='service_request', uselist=False)

class RejectionReason(db.Model):
    __tablename__ = 'rejection_reasons'
    
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reason = db.Column(db.Text)
    rejected_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    service_request = db.relationship('ServiceRequest', backref='rejection_reasons')
    professional = db.relationship('User', backref='rejections')

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rating = db.Column(db.Integer)  # 1-5
    comment = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class LocationUpdate(db.Model):
    __tablename__ = 'location_updates'
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    update_type = db.Column(db.String(20))  

    