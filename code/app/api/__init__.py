
from flask_restx import Api
from flask import Blueprint


api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_bp,
    title='Household Services API',
    version='1.0',
    description='API documentation for Household Services',
    doc='/docs'
)

auth_ns = api.namespace('auth', description='Authentication operations')
services_ns = api.namespace('services', description='Service operations')
requests_ns = api.namespace('requests', description='Service request operations')
users_ns = api.namespace('users', description='User operations')
