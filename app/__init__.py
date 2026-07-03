import os
from flask import Flask
from pathlib import Path

from .db import init_app as init_db_app, init_db


def create_app():
    app = Flask(__name__)

    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["DATABASE"] = str(BASE_DIR / "instance" / "gym_journal.sqlite")

    init_db_app(app)

    with app.app_context():
        init_db()

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes import main
    app.register_blueprint(main)

    return app
