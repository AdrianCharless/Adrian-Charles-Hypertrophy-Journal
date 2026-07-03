from flask import Flask
from pathlib import Path

from .db import init_app as init_db_app, init_db

from .auth import require_password


def create_app():
    app = Flask(__name__)
    @app.before_request
    def _auth_gate():
        return require_password()
    
    BASE_DIR = Path(__file__).resolve().parent.parent

    app.config["DATABASE"] = str(BASE_DIR / "instance" / "gym_journal.sqlite")

    init_db_app(app)

    with app.app_context():
        init_db()


    from .routes import main 
    app.register_blueprint(main)

    return app

