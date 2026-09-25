"""
app/__init__.py — Flask application factory.

Calling create_app() builds and returns a fully configured Flask app.
Using a factory function makes it easy to test different configurations.
"""

import os
from flask import Flask


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # Load configuration from config.py (which reads from .env)
    from config import Config
    app.config.from_object(Config)

    # ----------------------------------------------------------------
    # Register blueprints
    # ----------------------------------------------------------------

    from app.auth  import auth_bp
    from app.tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    # ----------------------------------------------------------------
    # Root index route
    # ----------------------------------------------------------------
    from flask import render_template, jsonify

    @app.route("/")
    def index():
        return render_template("index.html")

    # ----------------------------------------------------------------
    # DB connectivity test route (development helper)
    # ----------------------------------------------------------------
    @app.route("/db-test")
    def db_test():
        from app.models import get_connection
        from mysql.connector import Error
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return jsonify({
                "status": "success",
                "message": "MySQL connection is working.",
                "connected_database": db_name,
            })
        except Error as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return app
