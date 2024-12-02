

# app/api/routes/service_routes.py
from flask_restx import Resource
from ..models import service_model
from .. import services_ns
from ..models.service import Service

@services_ns.route('/')
class ServiceList(Resource):
    @services_ns.doc('list_services')
    @services_ns.marshal_list_with(service_model)
    def get(self):
        """List all services"""
        return Service.query.filter_by(is_active=True).all()

@services_ns.route('/<int:id>')
@services_ns.param('id', 'Service identifier')
class ServiceResource(Resource):
    @services_ns.doc('get_service')
    @services_ns.marshal_with(service_model)
    def get(self, id):
        """Get a specific service"""
        return Service.query.get_or_404(id)