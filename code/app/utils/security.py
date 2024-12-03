
from functools import wraps
from flask import abort, request, current_app, session
import hashlib
import hmac
import time
from flask_login import current_user
import os
from ..models.security import ActivityLog, FailedLoginAttempt
from .. import db 
from datetime import datetime, timedelta

class SecurityHeaders:
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        def security_headers(status, headers, exc_info=None):
            headers.extend([
                ('X-Frame-Options', 'SAMEORIGIN'),
                ('X-XSS-Protection', '1; mode=block'),
                ('X-Content-Type-Options', 'nosniff'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
                ('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data:;"),
                ('Referrer-Policy', 'strict-origin-when-cross-origin')
            ])
            return start_response(status, headers, exc_info)
        return self.app(environ, security_headers)

def rate_limit(max_requests, window_seconds=60):
    """Rate limiting decorator"""
    requests = {}
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time.time()
            client_ip = request.remote_addr
            requests_copy = requests.copy()
            for ip, data in requests_copy.items():
                if now - data['start_time'] > window_seconds:
                    del requests[ip]
            if client_ip not in requests:
                requests[client_ip] = {
                    'count': 1,
                    'start_time': now
                }
            else:
                if now - requests[client_ip]['start_time'] > window_seconds:
                    requests[client_ip] = {
                        'count': 1,
                        'start_time': now
                    }
                else:
                    requests[client_ip]['count'] += 1
                    
                    if requests[client_ip]['count'] > max_requests:
                        abort(429)  
            return f(*args, **kwargs)
        return wrapped
    return decorator

def check_content_type(content_type):

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.content_type != content_type:
                abort(415)  
            return f(*args, **kwargs)
        return wrapped
    return decorator

def verify_request_signature(f):
    """Verify request signature for API calls"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        signature = request.headers.get('X-Signature')
        if not signature:
            abort(401)
            
        body = request.get_data()
        timestamp = request.headers.get('X-Timestamp')
        
        expected_signature = hmac.new(
            current_app.config['API_SECRET_KEY'].encode(),
            f"{timestamp}.{body.decode()}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            abort(401)

        if abs(int(timestamp) - int(time.time())) > 300:  
            abort(401)
            
        return f(*args, **kwargs)
    return wrapped

class RoleRequired:
    """Role requirement decorator"""
    def __init__(self, *roles):
        self.roles = roles
        
    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in self.roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped

class CSRFProtection:
    def __init__(self, app):
        self.app = app
        
    def generate_token(self):
        if 'csrf_token' not in session:
            session['csrf_token'] = hashlib.sha256(os.urandom(32)).hexdigest()
        return session['csrf_token']
    
    def validate_token(self):
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            abort(403)

def sanitize_sql_input(value):
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

class AuditLogger:
    def __init__(self, app):
        self.app = app
        
    def log_activity(self, user_id, action, details=None):
        try:
            with self.app.app_context():
                log_entry = ActivityLog(
                    user_id=user_id,
                    action=action,
                    details=details,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.add(log_entry)
                db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log activity: {str(e)}")

class LoginAttemptTracker:
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = 900 
    
    @classmethod
    def record_failed_attempt(cls, email, ip_address):
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=cls.LOCKOUT_TIME)
        
        FailedLoginAttempt.query.filter(FailedLoginAttempt.timestamp < cutoff).delete()
        db.session.commit()
        attempt = FailedLoginAttempt(email=email, ip_address=ip_address)
        db.session.add(attempt)
        db.session.commit()
    
    @classmethod
    def is_blocked(cls, email, ip_address):
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=cls.LOCKOUT_TIME)
        
        attempt_count = FailedLoginAttempt.query.filter(
            FailedLoginAttempt.timestamp > cutoff,
            db.or_(
                FailedLoginAttempt.email == email,
                FailedLoginAttempt.ip_address == ip_address
            )
        ).count()
        
        return attempt_count >= cls.MAX_ATTEMPTS