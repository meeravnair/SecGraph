import os
from flask import Flask
from config import Config
from app.models import db, login_manager, AdminUser

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Custom template filters
    @app.template_filter('format_number')
    def format_number_filter(val):
        try:
            return f"{int(val):,}"
        except (ValueError, TypeError):
            return str(val) if val is not None else "0"

    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
