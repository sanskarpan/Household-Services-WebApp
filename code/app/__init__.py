
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .views import admin, auth, customer, professional, main, profile
    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(customer.bp)
    app.register_blueprint(professional.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(profile.bp)


    with app.app_context():
        db.create_all()
    return app