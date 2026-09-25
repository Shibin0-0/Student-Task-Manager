"""
config.py — Application configuration.

Reads all settings from the .env file using python-dotenv.
Never hardcode secrets here.
"""

import os
from dotenv import load_dotenv

# Load .env into environment variables
load_dotenv()


class Config:
    # Flask secret key — used to sign session cookies.
    # Set a long, random string in your .env file.
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-dev-key-change-in-production")

    # MySQL connection settings
    DB_HOST     = os.environ.get("DB_HOST", "localhost")
    DB_USER     = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME     = os.environ.get("DB_NAME", "student_task_manager")
