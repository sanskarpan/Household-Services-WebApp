# app/utils/validators.py
from wtforms import Form, StringField, PasswordField, TextAreaField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
import re
from datetime import datetime
class LoginForm(Form):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=50)
    ])

class RegistrationForm(Form):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80),
        # Custom validator for username format
        lambda form, field: check_username_format(field.data)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=50),
        # Custom validator for password strength
        lambda form, field: check_password_strength(field.data)
    ])
    location = StringField('Location', validators=[
        DataRequired(),
        Length(max=100)
    ])
    pin_code = StringField('PIN Code', validators=[
        DataRequired(),
        Length(min=5, max=10),
        # Custom validator for PIN code format
        lambda form, field: check_pin_code_format(field.data)
    ])

class ProfessionalRegistrationForm(RegistrationForm):
    service_type = SelectField('Service Type', coerce=int, validators=[
        DataRequired()
    ])
    experience = IntegerField('Years of Experience', validators=[
        DataRequired(),
        NumberRange(min=0, max=50)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=50, max=500)
    ])

class ServiceForm(Form):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    base_price = FloatField('Base Price', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    time_required = IntegerField('Time Required (minutes)', validators=[
        DataRequired(),
        NumberRange(min=15, max=480)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=50, max=500)
    ])

class ServiceRequestForm(Form):
    preferred_date = StringField('Preferred Date', validators=[
        DataRequired(),
        # Custom validator for date format and future date
        lambda form, field: check_future_date(field.data)
    ])
    location = StringField('Location', validators=[
        DataRequired(),
        Length(max=100)
    ])
    pin_code = StringField('PIN Code', validators=[
        DataRequired(),
        Length(min=5, max=10),
        lambda form, field: check_pin_code_format(field.data)
    ])
    remarks = TextAreaField('Remarks', validators=[
        Length(max=500)
    ])
    professional_id = IntegerField('Professional')

class ReviewForm(Form):
    rating = IntegerField('Rating', validators=[
        DataRequired(),
        NumberRange(min=1, max=5)
    ])
    comment = TextAreaField('Comment', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])

# Custom validation functions
def check_username_format(username):
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError('Username can only contain letters, numbers, and underscores')

def check_password_strength(password):
    if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{6,}$', password):
        raise ValidationError('Password must contain at least one letter, one number, and one special character')

def check_pin_code_format(pin_code):
    if not re.match(r'^\d{5,10}$', pin_code):
        raise ValidationError('Invalid PIN code format')

def check_future_date(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if date < datetime.now():
            raise ValidationError('Date must be in the future')
    except ValueError:
        raise ValidationError('Invalid date format')

# Sanitization functions
def sanitize_html(text):
    """Remove HTML tags from text"""
    return re.sub(r'<[^>]*?>', '', text)

def sanitize_script(text):
    """Remove potential script injections"""
    return re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)

def sanitize_input(text):
    """General input sanitization"""
    text = sanitize_html(text)
    text = sanitize_script(text)
    return text.strip()