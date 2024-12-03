
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .. import db

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            current_user.username = request.form['username']
            current_user.location = request.form['location']
            current_user.pin_code = request.form['pin_code']
            
            if current_user.role == 'professional':
                current_user.experience = request.form['experience']
                current_user.description = request.form['description']
            if request.form.get('new_password'):
                if current_user.check_password(request.form['current_password']):
                    current_user.set_password(request.form['new_password'])
                else:
                    flash('Current password is incorrect', 'error')
                    return redirect(url_for('profile.edit_profile'))
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.edit_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('profile/edit.html')
