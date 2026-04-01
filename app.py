<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, session
from supabase import create_client, Client
from datetime import date, datetime

SUPABASE_URL = "https://wnieylhcqjgjsrbdbhek.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InduaWV5bGhjcWpnanNyYmRiaGVrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5MDQ2NzksImV4cCI6MjA5MDQ4MDY3OX0.YOTxUR6L6qNMHURhAepyGPA4VKOq7_WVGPn551hWL94"

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Replace with a real secret key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create guest session if not already created
@app.before_request
def create_guest_session():
    if "user_id" not in session:
        auth_session = supabase.auth.sign_in_anonymously()
        session["user_id"] = auth_session.user.id


@app.route("/")
def index():
    return redirect("/board")


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

@app.route("/board")
def board():
    # Safely get the user_id from the session
    user_id = session.get("user_id")

    # If no user is logged in (like on Render), load all tasks
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

    # Add urgency to each row BEFORE grouping
    for r in rows:
        r["urgency"] = compute_urgency(r.get("due_date"))

    # Group tasks by status
    tasks = {
        "todo": [r for r in rows if r["status"] == "todo"],
        "in_progress": [r for r in rows if r["status"] == "in_progress"],
        "in_review": [r for r in rows if r["status"] == "in_review"],
        "done": [r for r in rows if r["status"] == "done"],
    }

    # Stats for the stats bar
    stats = {
        "total": len(rows),
        "completed": len(tasks["done"]),
        "overdue": len([r for r in rows if r.get("urgency") == "overdue"]),
        "due_soon": len([r for r in rows if r.get("urgency") == "soon"]),
    }

    return render_template("board.html", tasks=tasks, stats=stats)



@app.post("/add_task")
def add_task():
    title = request.form["title"]
    description = request.form.get("description")
    priority = request.form.get("priority", "normal")
    due_date = request.form.get("due_date")

    print("SESSION:", session)
    print("USER ID:", session.get("user_id"))

    # Safely get user_id
    user_id = session.get("user_id")

    # TEMP: allow adding tasks without login (Render)
    if not user_id:
        user_id = None

    supabase.table("tasks").insert({
        "title": title,
        "description": description,
        "status": "todo",
        "priority": priority,
        "due_date": due_date,
        "user_id": user_id   # ✔ use the safe fallback
    }).execute()

    return redirect("/board")


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

@app.post("/delete_task")
def delete_task():
    print("DELETE ROUTE HIT")
    print("FORM DATA:", request.form)

    task_id = request.form["id"].strip()

    result = supabase.table("tasks") \
        .delete() \
        .eq("id", task_id) \
        .eq("user_id", session["user_id"]) \
        .execute()

    print("DELETE RESULT:", result)

    return redirect("/board")


if __name__ == "__main__":
=======
from flask import Flask, render_template, request, redirect, session
from supabase import create_client, Client
from datetime import date, datetime

SUPABASE_URL = "https://wnieylhcqjgjsrbdbhek.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InduaWV5bGhjcWpnanNyYmRiaGVrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5MDQ2NzksImV4cCI6MjA5MDQ4MDY3OX0.YOTxUR6L6qNMHURhAepyGPA4VKOq7_WVGPn551hWL94"

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Replace with a real secret key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create guest session if not already created
@app.before_request
def create_guest_session():
    if "user_id" not in session:
        auth_session = supabase.auth.sign_in_anonymously()
        session["user_id"] = auth_session.user.id


@app.route("/")
def index():
    return redirect("/board")


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

@app.route("/board")
def board():
    response = supabase.table("tasks")\
        .select("*")\
        .eq("user_id", session["user_id"])\
        .execute()
    
    rows = response.data
    print("RESPONSE:", response)
    print("ROWS:", rows)

    # Add urgency to each row BEFORE grouping
    for r in rows:
        r["urgency"] = compute_urgency(r.get("due_date"))

    # group tasks by status
    tasks = {
        "todo": [r for r in rows if r["status"] == "todo"],
        "in_progress": [r for r in rows if r["status"] == "in_progress"],
        "in_review": [r for r in rows if r["status"] == "in_review"],
        "done": [r for r in rows if r["status"] == "done"],
    }

    stats = {
    "total": len(rows),
    "completed": len(tasks["done"]),
    "overdue": len([r for r in rows if r.get("urgency") == "overdue"]),
    "due_soon": len([r for r in rows if r.get("urgency") == "soon"]),
    }

    return render_template("board.html", tasks=tasks, stats=stats)


@app.post("/add_task")
def add_task():
    title = request.form["title"]
    description = request.form.get("description")
    priority = request.form.get("priority","normal")
    due_date = request.form.get("due_date")

    print("SESSION:", session)
    print("USER ID:", session.get("user_id"))



    supabase.table("tasks").insert({
        "title": title,
        "description" : description,
        "status": "todo",
        "priority": priority,
        "due_date": due_date,
        "user_id": session["user_id"]
    }).execute()

    return redirect("/board")


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

@app.post("/delete_task")
def delete_task():
    print("DELETE ROUTE HIT")
    print("FORM DATA:", request.form)

    task_id = request.form["id"].strip()

    result = supabase.table("tasks") \
        .delete() \
        .eq("id", task_id) \
        .eq("user_id", session["user_id"]) \
        .execute()

    print("DELETE RESULT:", result)

    return redirect("/board")


if __name__ == "__main__":
>>>>>>> ab99b70359aa4ff72642b9c6000a9356541eac4e
    app.run(debug=True)