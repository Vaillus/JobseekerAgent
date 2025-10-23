from flask import Flask
from jobseeker_agent.corrector.interface.routes import bp


def create_app():
    # Using `__name__` is the standard way for Flask to locate resources.
    # The blueprint already handles its own templates and static files.
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
