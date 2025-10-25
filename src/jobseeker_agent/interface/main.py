import sys
import webbrowser
import threading
import os
from pathlib import Path
from flask import Flask

print("--- Script starting ---")

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
print(f"Project root added to sys.path: {project_root}")

from jobseeker_agent.interface.blueprints.reviewer import bp as reviewer_bp
from jobseeker_agent.interface.blueprints.customizer import bp as customizer_bp

print("--- Initializing Flask App ---")
# Get the interface directory path
interface_path = Path(__file__).resolve().parent

# Create Flask app with template and static folders
app = Flask(
    __name__,
    template_folder=str(interface_path / "templates"),
    static_folder=str(interface_path / "static"),
)

# Register blueprints
app.register_blueprint(reviewer_bp)  # No prefix - it's at the root
app.register_blueprint(customizer_bp, url_prefix="/customizer")

# Disable caching for development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

print("Flask App initialized.")


def main():
    """Main function to run the Flask app."""
    print("--- main() function called ---")
    # We use a thread to open the browser after the server starts.
    # This should only happen in the main process, not in the reloader's child process.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000/")).start()
    print("Starting the dashboard server at http://127.0.0.1:5000/")
    print("Press CTRL+C to stop the server.")
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    print("--- Script executed directly ---")
    main()

