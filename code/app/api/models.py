from flask_restx import fields
from . import api

login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

register_model = api.model('Register', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password'),
    'role': fields.String(required=True, enum=['customer', 'professional'], description='User role'),
    'location': fields.String(required=True, description='User location'),
    'pin_code': fields.String(required=True, description='PIN code')
})

service_model = api.model('Service', {
    'id': fields.Integer(description='Service ID'),
    'name': fields.String(required=True, description='Service name'),
    'base_price': fields.Float(required=True, description='Base price'),
    'time_required': fields.Integer(required=True, description='Time required in minutes'),
    'description': fields.String(required=True, description='Service description')
})

service_request_model = api.model('ServiceRequest', {
    'service_id': fields.Integer(required=True, description='Service ID'),
    'preferred_date': fields.DateTime(required=True, description='Preferred service date'),
    'location': fields.String(required=True, description='Service location'),
    'pin_code': fields.String(required=True, description='Location PIN code'),
    'remarks': fields.String(description='Additional remarks')
})