from flask import Flask
from jobseeker_agent.corrector.interface.routes import bp


def create_app():
    # Using `__name__` is the standard way for Flask to locate resources.
    # The blueprint already handles its own templates and static files.
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


def main():
    """Main function to run the Flask app."""
    app = create_app()
    url = "http://127.0.0.1:5001/"
    print(f"Starting the dashboard server at {url}")
    print("Press CTRL+C to stop the server.")
    app.run(port=5001, debug=True)


if __name__ == "__main__":
    main()
