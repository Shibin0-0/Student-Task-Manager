"""
run.py — Entry point for the Student Task Manager.

Run the development server with:
    python run.py

On startup this also tests the MySQL connection so you can catch
misconfiguration before the server begins accepting requests.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    from app.models import test_connection
    test_connection()
    app.run(debug=True)
