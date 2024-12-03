
from .. import db
from datetime import datetime

class ProfessionalDocument(db.Model):
    __tablename__ = 'professional_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    document_type = db.Column(db.String(50)) 
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    verification_note = db.Column(db.Text)
    
    professional = db.relationship('User', backref='documents')