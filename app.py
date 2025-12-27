from flask import Flask, render_template, request, redirect
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE,
            completed BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    sort = request.args.get("sort")
    order = ""
    if sort == "created_new":
        order = "ORDER BY created_at DESC"
    elif sort == "created_old":
        order = "ORDER BY created_at ASC"
    elif sort == "due_near":
        order = "ORDER BY due_date ASC"
    elif sort == "due_far":
        order = "ORDER BY due_date DESC"

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(f"SELECT * FROM tasks WHERE completed = FALSE {order}")
    tasks = cur.fetchall()
    cur.execute(f"SELECT * FROM tasks WHERE completed = TRUE {order}")
    completed_tasks = cur.fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=None)

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, due_date) VALUES (%s, %s)", (title, due_date))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT completed FROM tasks WHERE id=%s", (task_id,))
    current = cur.fetchone()
    if current:
        cur.execute("UPDATE tasks SET completed=%s WHERE id=%s", (not current[0], task_id))
        conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:task_id>")
def edit(task_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM tasks WHERE completed = FALSE")
    tasks = cur.fetchall()
    cur.execute("SELECT * FROM tasks WHERE completed = TRUE")
    completed_tasks = cur.fetchall()
    cur.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    editing_task = cur.fetchone()
    conn.close()
    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=editing_task)

@app.route("/update/<int:task_id>", methods=["POST"])
def update(task_id):
    new_title = request.form.get("title")
    new_due_date = request.form.get("due_date") or None
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET title=%s, due_date=%s WHERE id=%s", (new_title, new_due_date, task_id))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)




