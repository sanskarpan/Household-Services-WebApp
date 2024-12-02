# app/utils/upload.py
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_document(file, user_id):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create unique filename
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{user_id}_{int(datetime.utcnow().timestamp())}{ext}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        return file_path
    return None