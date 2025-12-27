import os
from flask import Flask, render_template, request, redirect
import psycopg2
import psycopg2.extras

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

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
        );
    """)
    conn.commit()
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
        order = "ORDER BY due_date ASC NULLS LAST"
    elif sort == "due_far":
        order = "ORDER BY due_date DESC NULLS LAST"

    conn = get_db()
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM tasks WHERE completed = false {order}")
    tasks = cur.fetchall()

    cur.execute(f"SELECT * FROM tasks WHERE completed = true {order}")
    completed_tasks = cur.fetchall()

    conn.close()

    return render_template(
        "index.html",
        tasks=tasks,
        completed_tasks=completed_tasks,
        editing_task=None
    )

# 以下 add / delete / complete / edit / update は今のままでOK
# （DB接続だけ get_db() を使っていれば動きます）

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)


