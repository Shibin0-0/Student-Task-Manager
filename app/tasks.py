"""
app/tasks.py — Task management blueprint.

Routes:
    GET  /dashboard              — stats overview
    GET  /tasks                  — list all tasks for the logged-in user
    GET  POST /tasks/create      — create a new task
    GET  POST /tasks/<id>/edit   — edit an existing task
    POST /tasks/<id>/delete      — delete a task (form POST from list page)
    POST /tasks/<id>/toggle      — toggle pending ↔ completed
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
)
from app.utils import login_required
from app.models import (
    create_task,
    get_tasks_by_user,
    get_task_by_id,
    update_task,
    delete_task,
    toggle_task_status,
    get_task_stats,
)

# No URL prefix — routes live at /dashboard, /tasks, etc.
tasks_bp = Blueprint("tasks", __name__)


# ================================================================
# Dashboard
# ================================================================

@tasks_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Show a summary of the logged-in user's tasks.
    Displays total, completed, pending counts and a completion percentage.
    """
    user_id = session["user_id"]
    stats   = get_task_stats(user_id)
    return render_template("tasks/dashboard.html", stats=stats)


# ================================================================
# Task list
# ================================================================

@tasks_bp.route("/tasks")
@login_required
def task_list():
    """
    Display all tasks belonging to the logged-in user.
    """
    user_id = session["user_id"]
    tasks   = get_tasks_by_user(user_id)
    return render_template("tasks/list.html", tasks=tasks)


# ================================================================
# Create task
# ================================================================

@tasks_bp.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task_view():
    """
    GET  — show the create-task form.
    POST — validate input, insert task, redirect to task list.
    """
    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date    = request.form.get("due_date", "").strip() or None

        # --- Validation ---
        errors = []
        if not title:
            errors.append("Task title is required.")
        elif len(title) > 200:
            errors.append("Task title must be 200 characters or fewer.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "tasks/create.html",
                title=title,
                description=description,
                due_date=due_date,
            )

        user_id = session["user_id"]
        create_task(user_id, title, description, due_date)

        flash("Task created successfully!", "success")
        return redirect(url_for("tasks.task_list"))

    # GET — empty form
    return render_template("tasks/create.html")


# ================================================================
# Edit task
# ================================================================

@tasks_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task_view(task_id):
    """
    GET  — show the edit form pre-filled with the task's current values.
    POST — validate, update the task, redirect to task list.

    Returns 403 if the task does not belong to the logged-in user.
    """
    user_id = session["user_id"]

    # Ownership check — get_task_by_id returns None if not owned
    task = get_task_by_id(task_id, user_id)
    if task is None:
        abort(403)   # Forbidden — task doesn't exist or isn't theirs

    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date    = request.form.get("due_date", "").strip() or None
        status      = request.form.get("status", "pending")

        # Sanitize status — only allow known values
        if status not in ("pending", "completed"):
            status = "pending"

        # --- Validation ---
        errors = []
        if not title:
            errors.append("Task title is required.")
        elif len(title) > 200:
            errors.append("Task title must be 200 characters or fewer.")

        if errors:
            for error in errors:
                flash(error, "danger")
            # Pass form values back so the user doesn't lose their input
            task["title"]       = title
            task["description"] = description
            task["due_date"]    = due_date
            task["status"]      = status
            return render_template("tasks/edit.html", task=task)

        update_task(task_id, user_id, title, description, due_date, status)

        flash("Task updated successfully!", "success")
        return redirect(url_for("tasks.task_list"))

    # GET — show form with existing values
    return render_template("tasks/edit.html", task=task)


# ================================================================
# Delete task
# ================================================================

@tasks_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task_view(task_id):
    """
    POST-only — delete the task if it belongs to the logged-in user.

    The JavaScript confirmation dialog in main.js prevents accidental deletes.
    Using POST (not GET) prevents deletion triggered by link prefetchers.

    Returns 403 if the task does not belong to the logged-in user.
    """
    user_id      = session["user_id"]
    rows_deleted = delete_task(task_id, user_id)

    if rows_deleted == 0:
        # Task not found or not owned — return 403
        abort(403)

    flash("Task deleted.", "info")
    return redirect(url_for("tasks.task_list"))


# ================================================================
# Toggle task status
# ================================================================

@tasks_bp.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task_view(task_id):
    """
    POST-only — flip a task's status between pending and completed.

    Redirects back to the task list after toggling.
    Returns 403 if the task does not belong to the logged-in user.
    """
    user_id      = session["user_id"]
    rows_updated = toggle_task_status(task_id, user_id)

    if rows_updated == 0:
        abort(403)

    return redirect(url_for("tasks.task_list"))
