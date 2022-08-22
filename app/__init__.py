import os
import datetime
from json import JSONEncoder

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

from app.cache import Cache
from app.config import SLACK_API_TOKEN, SLACK_SIGNING_SECRET, SQLALCHEMY_DATABASE_URI
db = SQLAlchemy()
migrate = Migrate()
client = WebClient(token=SLACK_API_TOKEN) #os.environ["SLACK_API_TOKEN"])
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)#os.environ["SLACK_SIGNING_SECRET"])

# redis_client = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379), db=0)
app_cache = Cache()


class Config:
    # General Config
    # SECRET_KEY = environ.get('SECRET_KEY')
    # FLASK_APP = environ.get('FLASK_APP')
    # FLASK_ENV = environ.get('FLASK_ENV')

    # Database
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI #os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Custom encoder to serialize datetime objects
class StandupJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            return obj.strftime("%H:%M")


def create_app():
    """
    Construct the core application.
    """
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config())
    app.json_encoder = StandupJSONEncoder

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
