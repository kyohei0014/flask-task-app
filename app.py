from flask import Flask, render_template, request, redirect
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# --------------------
# DB 接続
# --------------------
DATABASE_URL = os.environ.get("DATABASE_URL")  # Renderの環境変数

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

# --------------------
# DB 初期化
# --------------------
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


# --------------------
# ホーム画面
# --------------------
@app.route("/")
def index():
    sort = request.args.get("sort")

    base_query = "SELECT * FROM tasks"
    completed_query = base_query + " WHERE completed = TRUE"
    uncompleted_query = base_query + " WHERE completed = FALSE"

    # 並び替え
    if sort == "created_new":
        order = " ORDER BY created_at DESC"
    elif sort == "created_old":
        order = " ORDER BY created_at ASC"
    elif sort == "due_near":
        order = " ORDER BY due_date ASC"
    elif sort == "due_far":
        order = " ORDER BY due_date DESC"
    else:
        order = ""

    conn = get_db()
    uncompleted = conn.cursor()
    uncompleted.execute(uncompleted_query + order)
    uncompleted_tasks = uncompleted.fetchall()

    completed = conn.cursor()
    completed.execute(completed_query + order)
    completed_tasks = completed.fetchall()

    conn.close()
    return render_template(
        "index.html",
        tasks=uncompleted_tasks,
        completed_tasks=completed_tasks
    )

# --------------------
# 追加
# --------------------
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, due_date) VALUES (%s, %s)",
        (title, due_date)
    )
    conn.commit()
    conn.close()
    return redirect("/")


# --------------------
# 削除
# --------------------
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit()
    conn.close()
    return redirect("/")


# --------------------
# 完了 / 取消
# --------------------
@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT completed FROM tasks WHERE id=%s", (task_id,))
    current = cur.fetchone()
    if current:
        new_value = not current["completed"]
        cur.execute("UPDATE tasks SET completed=%s WHERE id=%s", (new_value, task_id))
        conn.commit()
    conn.close()
    return redirect("/")


# --------------------
# 編集
# --------------------
@app.route("/edit/<int:task_id>")
def edit(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE completed=FALSE")
    tasks = cur.fetchall()
    cur.execute("SELECT * FROM tasks WHERE completed=TRUE")
    completed_tasks = cur.fetchall()
    cur.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    editing_task = cur.fetchone()
    conn.close()
    return render_template(
        "index.html",
        tasks=tasks,
        completed_tasks=completed_tasks,
        editing_task=editing_task
    )


# --------------------
# 更新
# --------------------
@app.route("/update/<int:task_id>", methods=["POST"])
def update(task_id):
    new_title = request.form.get("title", "").strip()
    new_due_date = request.form.get("due_date") or None

    if not new_title:
        return redirect(f"/edit/{task_id}")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title=%s, due_date=%s WHERE id=%s",
        (new_title, new_due_date, task_id)
    )
    conn.commit()
    conn.close()
    return redirect("/")


# --------------------
# 起動
# --------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)



