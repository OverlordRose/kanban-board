import os
from flask import Flask, render_template, request, redirect, session
from supabase import create_client, Client
from datetime import date, datetime
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Create guest session safely
# -----------------------------
@app.before_request
def create_guest_session():
    if not session.get("user_id"):
        # Always generate a stable local UUID for this guest
        user_id = str(uuid4())
        session["user_id"] = user_id
        print("Created guest session:", user_id)
        
# -----------------------------
# Home → redirect to board
# -----------------------------
@app.route("/")
def index():
    return redirect("/board")


# -----------------------------
# Urgency calculation
# -----------------------------
def compute_urgency(due_date_str):
    if not due_date_str or due_date_str.strip() == "":
        return None

    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        return None  # invalid date format

    today = date.today()
    diff = (due - today).days

    if diff < 0:
        return "overdue"
    elif diff == 0:
        return "today"
    elif diff <= 3:
        return "soon"
    else:
        return None

# -----------------------------
# Board route
# -----------------------------
@app.route("/board")
def board():
    # Get the user_id from the Flask session
    user_id = session.get("user_id")
    if not user_id:
        print("ERROR: No session user_id")
        return redirect("/login")

    # Fetch only this user's tasks (RLS requires this)
    response = (
        supabase.table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    rows = response.data or []

    # Add urgency
    for r in rows:
        r["urgency"] = compute_urgency(r.get("due_date"))

    # Group tasks
    tasks = {
        "todo": [r for r in rows if r["status"] == "todo"],
        "in_progress": [r for r in rows if r["status"] == "in_progress"],
        "in_review": [r for r in rows if r["status"] == "in_review"],
        "done": [r for r in rows if r["status"] == "done"],
    }

    # Stats
    stats = {
        "total": len(rows),
        "completed": len(tasks["done"]),
        "overdue": len([r for r in rows if r.get("urgency") == "overdue"]),
        "due_today": len([r for r in rows if r.get("urgency") == "today"]),
        "due_soon": len([r for r in rows if r.get("urgency") == "soon"]),
    }

    return render_template("board.html", tasks=tasks, stats=stats)

# -----------------------------
# Add task
# -----------------------------
@app.post("/add_task")
def add_task():
    title = request.form.get("title")
    description = request.form.get("description")
    priority = request.form.get("priority", "normal")
    due_date = request.form.get("due_date") or None

    user_id = session.get("user_id")
    if not user_id:
        print("ERROR: No session user_id")
        return redirect("/login")
    

    supabase.table("tasks").insert({
        "title": title,
        "description": description,
        "status": "todo",
        "priority": priority,
        "due_date": due_date,
        "user_id": user_id
    }).execute()

    return redirect("/board")


# -----------------------------
# Update status
# -----------------------------
@app.post("/update_status")
def update_status():
    data = request.get_json()
    task_id = data.get("id")
    new_status = data.get("status")

    # Get user_id from Flask session
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "No session user_id"}, 400

    # Update only if the task belongs to this user (RLS requirement)
    supabase.table("tasks") \
        .update({"status": new_status}) \
        .eq("id", task_id) \
        .eq("user_id", user_id) \
        .execute()

    return {"success": True}


# -----------------------------
# Edit task
# -----------------------------
@app.post("/edit_task")
def edit_task():
    task_id = request.form.get("id")
    new_title = request.form.get("title")
    new_description = request.form.get("description")
    new_due_date = request.form.get("due_date") or None

    user_id = session.get("user_id")
    if not user_id:
        print("ERROR: No session user_id")
        return redirect("/login")

    supabase.table("tasks") \
        .update({
            "title": new_title,
            "description": new_description,
            "due_date": new_due_date
        }) \
        .eq("id", task_id) \
        .eq("user_id", user_id) \
        .execute()

    return redirect("/board")

# -----------------------------
# Delete task
# -----------------------------
@app.post("/delete_task")
def delete_task():
    task_id = request.form.get("id", "").strip()

    user_id = session.get("user_id")
    if not user_id:
        print("ERROR: No session user_id")
        return redirect("/login")

    # Delete only if the task belongs to this user (RLS requirement)
    supabase.table("tasks") \
        .delete() \
        .eq("id", task_id) \
        .eq("user_id", user_id) \
        .execute()

    return redirect("/board")

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)