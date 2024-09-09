from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)


    from app.main import main
    app.register_blueprint(main, url_prefix='/main')

    from app.ml import ml
    app.register_blueprint(ml, url_prefix='/ml')


    return app