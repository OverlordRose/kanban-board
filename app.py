
from flask import Flask, render_template, request, redirect, session
from supabase import create_client, Client
from datetime import date, datetime

SUPABASE_URL = "https://wnieylhcqjgjsrbdbhek.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InduaWV5bGhjcWpnanNyYmRiaGVrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5MDQ2NzksImV4cCI6MjA5MDQ4MDY3OX0.YOTxUR6L6qNMHURhAepyGPA4VKOq7_WVGPn551hWL94"

app = Flask(__name__)
app.secret_key = "your-secret-key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# Create guest session
# -----------------------------
@app.before_request
def create_guest_session():
    if "user_id" not in session:
        auth_session = supabase.auth.sign_in_anonymously()
        session["user_id"] = auth_session.user.id


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
    if not due_date_str:
        return None

    due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
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
    user_id = session.get("user_id")

    if not user_id:
        response = supabase.table("tasks").select("*").execute()
    else:
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
        "due_soon": len([r for r in rows if r.get("urgency") == "soon"]),
    }

    return render_template("board.html", tasks=tasks, stats=stats)


# -----------------------------
# Add task
# -----------------------------
@app.post("/add_task")
def add_task():
    title = request.form["title"]
    description = request.form.get("description")
    priority = request.form.get("priority", "normal")
    due_date = request.form.get("due_date")

    user_id = session.get("user_id")

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
    task_id = data["id"]
    new_status = data["status"]

    supabase.table("tasks") \
        .update({"status": new_status}) \
        .eq("id", task_id) \
        .eq("user_id", session["user_id"]) \
        .execute()

    return {"success": True}


# -----------------------------
# Edit task
# -----------------------------
@app.post("/edit_task")
def edit_task():
    task_id = request.form["id"]
    new_title = request.form["title"]

    supabase.table("tasks") \
        .update({"title": new_title}) \
        .eq("id", task_id) \
        .eq("user_id", session["user_id"]) \
        .execute()

    return redirect("/board")


# -----------------------------
# Delete task
# -----------------------------
@app.post("/delete_task")
def delete_task():
    task_id = request.form["id"].strip()

    supabase.table("tasks") \
        .delete() \
        .eq("id", task_id) \
        .eq("user_id", session["user_id"]) \
        .execute()

    return redirect("/board")


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)