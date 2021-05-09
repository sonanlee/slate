import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.cache import Cache

db = SQLAlchemy()
migrate = Migrate()

# redis_client = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379), db=0)
app_cache = cache.Cache()


def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    with app.app_context():
        from . import routes
        db.create_all()
        init_cache()

        return app


def init_cache():
    from app.models import Auth

    keys = Auth.query.all()

    for key in keys:
        if key.token and key.user:
            app_cache.set(key.token, key.user)

