import os 
import hashlib
from .. import db
from datetime import datetime

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activity_logs')

class FailedLoginAttempt(db.Model):
    __tablename__ = 'failed_login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class BlockedIP(db.Model):
    __tablename__ = 'blocked_ips'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True)
    reason = db.Column(db.String(200))
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    key = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='api_keys')

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.key = hashlib.sha256(os.urandom(32)).hexdigest()