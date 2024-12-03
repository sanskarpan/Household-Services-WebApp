
from app import create_app, db
from app.models.user import User
from app.models.service import Service, ServiceRequest, Review
from flask_migrate import Migrate
import click

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Service': Service,
        'ServiceRequest': ServiceRequest,
        'Review': Review
    }

@app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        click.echo('Initialized the database.')

@app.cli.command('create-admin')
@click.argument('email')
@click.argument('username')
@click.argument('password')
def create_admin(email, username, password):
    """Create an admin user"""
    with app.app_context():
        if User.query.filter_by(email=email).first():
            click.echo('This Email has been already registered')
            return
        
        if User.query.filter_by(username=username).first():
            click.echo('Username already taken')
            return
        
        user = User(
            email=email,
            username=username,
            role='admin',
            is_active=True,
            location='Admin Location',
            pin_code='000000'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        click.echo('Admin user created successfully')

@app.cli.command('create-sample-data')
def create_sample_data():
    """Create sample data for testing"""
    with app.app_context():
        # Create services
        services = [
            {
                'name': 'Plumbing',
                'base_price': 100.00,
                'time_required': 60,
                'description': 'Professional plumbing services including repairs and installations',
                'is_active': True
            },
            {
                'name': 'Electrical',
                'base_price': 120.00,
                'time_required': 90,
                'description': 'Electrical repairs and installations by certified electricians',
                'is_active': True
            },
            {
                'name': 'Carpentry',
                'base_price': 150.00,
                'time_required': 120,
                'description': 'Custom carpentry work and furniture repairs',
                'is_active': True
            },
            {
                'name': 'House Cleaning',
                'base_price': 80.00,
                'time_required': 180,
                'description': 'Professional house cleaning services',
                'is_active': True
            }
        ]
        
        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)
        
        try:
            db.session.commit()
            click.echo('Sample services created successfully')
        except Exception as e:
            db.session.rollback()
            click.echo(f'Error creating sample data: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True)

