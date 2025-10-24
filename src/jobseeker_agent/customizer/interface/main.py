from flask import Flask
from jobseeker_agent.corrector.interface.routes import bp


def create_app():
    # Using `__name__` is the standard way for Flask to locate resources.
    # The blueprint already handles its own templates and static files.
    app = Flask(__name__)
    # We add the prefix here to make the standalone app behave like the integrated one
    app.register_blueprint(bp, url_prefix="/corrector")
    return app

if __name__ == "__main__":
    app = create_app()
    # Note: Running standalone requires manually navigating to a job URL
    # to set the context for the application.
    # For example: http://127.0.0.1:5001/corrector/apply/71
    print("Corrector dashboard running. Please navigate to /corrector/apply/<job_id>")
    print("Example: http://127.0.0.1:5001/corrector/apply/71")
    app.run(port=5001, debug=True)


