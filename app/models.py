"""
app/models.py — Database connection layer and query helpers.

All functions use:
  - Parameterized queries (%s placeholders) to prevent SQL injection.
  - try/finally blocks to guarantee connections are always closed.
  - dictionary=True cursors so rows are returned as dicts (easier to use).

Ownership rule: every task query that touches a specific task includes
BOTH task_id AND user_id in the WHERE clause. This means even if a user
guesses someone else's task ID, they cannot read, edit, or delete it.
"""

import mysql.connector
from mysql.connector import Error
from flask import current_app


# ================================================================
# Connection helper
# ================================================================

def get_connection():
    """
    Create and return a new MySQL database connection.

    Reads host, user, password, and database name from the Flask app
    configuration (which in turn reads from .env via config.py).

    Raises:
        mysql.connector.Error — if the connection cannot be established.
    """
    return mysql.connector.connect(
        host=current_app.config["DB_HOST"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"],
    )


def test_connection():
    """
    Attempt a single connection to verify the database is reachable.
    Prints a terminal message and returns True on success, False on failure.
    Called once at startup from run.py.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            print("✅  MySQL connection successful — database is reachable.")
            return True
        except Error as e:
            print(f"❌  MySQL connection failed: {e}")
            return False


# ================================================================
# User queries
# ================================================================

def create_user(name, email, password_hash):
    """
    Insert a new user into the users table.

    Returns:
        int — the new user's auto-generated id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email):
    """
    Return the user row matching the given email, or None.

    Returns dict keys: id, name, email, password_hash, created_at
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    """
    Return the user row matching the given primary key, or None.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ================================================================
# Task queries
# ================================================================

def create_task(user_id, title, description, due_date):
    """
    Insert a new task for the given user.

    Parameters:
        user_id     -- the logged-in user's id (from session)
        title       -- task title string
        description -- optional text (may be empty string or None)
        due_date    -- datetime.date object or None

    Returns:
        int — the new task's auto-generated id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, description, due_date, status)
            VALUES (%s, %s, %s, %s, 'pending')
            """,
            (user_id, title, description or None, due_date or None),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_tasks_by_user(user_id):
    """
    Return all tasks belonging to user_id, ordered newest first.

    Returns:
        list of dicts — each dict is a task row.
        Keys: id, user_id, title, description, status, due_date, created_at
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, user_id, title, description, status, due_date, created_at
            FROM   tasks
            WHERE  user_id = %s
            ORDER  BY created_at DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_task_by_id(task_id, user_id):
    """
    Return a single task, but ONLY if it belongs to user_id.

    The double WHERE condition (id AND user_id) is the ownership check:
    a user cannot fetch another user's task — even if they guess the id.

    Returns:
        dict — the task row, or None if not found / not owned.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, user_id, title, description, status, due_date, created_at
            FROM   tasks
            WHERE  id = %s AND user_id = %s
            """,
            (task_id, user_id),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def update_task(task_id, user_id, title, description, due_date, status):
    """
    Update a task's fields — only if it belongs to user_id.

    Returns:
        int — number of rows affected (0 means task not found or not owned).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE tasks
            SET    title       = %s,
                   description = %s,
                   due_date    = %s,
                   status      = %s
            WHERE  id = %s AND user_id = %s
            """,
            (title, description or None, due_date or None, status, task_id, user_id),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def delete_task(task_id, user_id):
    """
    Delete a task — only if it belongs to user_id.

    Returns:
        int — number of rows deleted (0 means task not found or not owned).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, user_id),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def toggle_task_status(task_id, user_id):
    """
    Switch a task's status between 'pending' and 'completed'.

    Uses a CASE expression so the toggle happens in a single query —
    no need to read the current status first.

    Returns:
        int — number of rows updated (0 means task not found or not owned).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE tasks
            SET    status = CASE
                                WHEN status = 'pending'   THEN 'completed'
                                WHEN status = 'completed' THEN 'pending'
                                ELSE 'pending'
                            END
            WHERE  id = %s AND user_id = %s
            """,
            (task_id, user_id),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def get_task_stats(user_id):
    """
    Return summary statistics for the logged-in user's tasks.

    Returns:
        dict with keys:
            total      -- int, total number of tasks
            completed  -- int, tasks with status='completed'
            pending    -- int, tasks with status='pending'
            percentage -- int, completion percentage (0–100)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                COUNT(*)                                              AS total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending
            FROM tasks
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        total     = int(row["total"]     or 0)
        completed = int(row["completed"] or 0)
        pending   = int(row["pending"]   or 0)
        percentage = round((completed / total) * 100) if total > 0 else 0
        return {
            "total":      total,
            "completed":  completed,
            "pending":    pending,
            "percentage": percentage,
        }
    finally:
        cursor.close()
        conn.close()
