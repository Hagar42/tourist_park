import os

from flask import Flask, render_template, request, redirect, url_for, flash

from models import (
    init_db, get_tasks, get_task, create_task, update_task, delete_task,
    get_locations, create_location, delete_location,
    get_staff, create_staff, toggle_staff_active,
    get_dashboard_stats,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

# Initialise database at startup
init_db()


# ── Dashboard ──────────────────────────────────────────────

@app.route("/")
def dashboard():
    stats = get_dashboard_stats()
    urgent_tasks = get_tasks(priority="urgent")
    recent_tasks = get_tasks()[:10]
    return render_template("dashboard.html", stats=stats, urgent_tasks=urgent_tasks, recent_tasks=recent_tasks)


# ── Tasks ──────────────────────────────────────────────────

@app.route("/tasks")
def task_list():
    status = request.args.get("status")
    category = request.args.get("category")
    priority = request.args.get("priority")
    tasks = get_tasks(status=status, category=category, priority=priority)
    locations = get_locations()
    staff = get_staff()
    return render_template("tasks.html", tasks=tasks, locations=locations, staff=staff,
                           current_status=status, current_category=category, current_priority=priority)


@app.route("/tasks/new", methods=["GET", "POST"])
def task_new():
    if request.method == "POST":
        create_task(request.form)
        flash("Task created successfully.", "success")
        return redirect(url_for("task_list"))
    locations = get_locations()
    staff = get_staff()
    return render_template("task_form.html", task=None, locations=locations, staff=staff)


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def task_edit(task_id):
    task = get_task(task_id)
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("task_list"))
    if request.method == "POST":
        update_task(task_id, request.form)
        flash("Task updated.", "success")
        return redirect(url_for("task_list"))
    locations = get_locations()
    staff = get_staff()
    return render_template("task_form.html", task=task, locations=locations, staff=staff)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def task_delete(task_id):
    delete_task(task_id)
    flash("Task deleted.", "success")
    return redirect(url_for("task_list"))


@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def task_status(task_id):
    task = get_task(task_id)
    if task:
        task["status"] = request.form["status"]
        update_task(task_id, task)
        flash(f"Task marked as {request.form['status']}.", "success")
    return redirect(request.referrer or url_for("task_list"))


# ── Locations ──────────────────────────────────────────────

@app.route("/locations")
def location_list():
    locations = get_locations()
    return render_template("locations.html", locations=locations)


@app.route("/locations/new", methods=["POST"])
def location_new():
    create_location(request.form)
    flash("Location added.", "success")
    return redirect(url_for("location_list"))


@app.route("/locations/<int:loc_id>/delete", methods=["POST"])
def location_delete(loc_id):
    delete_location(loc_id)
    flash("Location deleted.", "success")
    return redirect(url_for("location_list"))


# ── Staff ──────────────────────────────────────────────────

@app.route("/staff")
def staff_list():
    staff = get_staff(active_only=False)
    return render_template("staff.html", staff=staff)


@app.route("/staff/new", methods=["POST"])
def staff_new():
    create_staff(request.form)
    flash("Staff member added.", "success")
    return redirect(url_for("staff_list"))


@app.route("/staff/<int:staff_id>/toggle", methods=["POST"])
def staff_toggle(staff_id):
    toggle_staff_active(staff_id)
    flash("Staff status updated.", "success")
    return redirect(url_for("staff_list"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
