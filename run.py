"""
run.py — Entry point for the Student Task Manager.

Run the development server with:
    python run.py

On startup this also tests the MySQL connection so you can catch
misconfiguration before the server begins accepting requests.
"""

from app import create_app
from app.models import test_connection

# Verify database connectivity before starting the server.
# The result is printed to the terminal — check there for ✅ or ❌.
test_connection()

app = create_app()

if __name__ == "__main__":
    # debug=True reloads the server automatically when you save a file.
    # Turn this OFF in a real production deployment.
    app.run(debug=True)
