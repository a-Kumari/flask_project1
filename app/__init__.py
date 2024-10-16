from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from flask_jwt_extended import JWTManager
from flask_mail import Mail


db = SQLAlchemy()
migrate = Migrate()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    jwt = JWTManager(app)

    db.init_app(app)
    migrate.init_app(app,db)
    mail.init_app(app)

    from .models import User, Product, Order, CartItem
    from .routes import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/api')

    return app

