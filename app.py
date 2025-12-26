# app.py (PostgreSQL 版)

from flask import Flask, render_template, request, redirect
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# --------------------
# DB 接続
# --------------------
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    # 辞書型で行にアクセスできる
    conn.cursor_factory = psycopg2.extras.RealDictCursor
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
            created_at TIMESTAMP DEFAULT NOW(),
            due_date DATE,
            completed BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    cur.close()
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
    cur = conn.cursor()
    cur.execute(uncompleted_query + order)
    uncompleted = cur.fetchall()
    cur.execute(completed_query + order)
    completed = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", tasks=uncompleted, completed_tasks=completed)

# --------------------
# 追加
# --------------------
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title")
    due_date = request.form.get("due_date")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, created_at, due_date, completed)
        VALUES (%s, NOW(), %s, FALSE)
    """, (title, due_date if due_date else None))
    conn.commit()
    cur.close()
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
    cur.close()
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
    cur.close()
    conn.close()
    return redirect("/")

# --------------------
# 編集（同じ画面で表示）
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
    cur.close()
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
    new_due_date = request.form.get("due_date", "").strip()

    if not new_title:
        return redirect(f"/edit/{task_id}")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title=%s, due_date=%s WHERE id=%s",
        (new_title, new_due_date if new_due_date else None, task_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")

# --------------------
# 起動（ローカル用）
# --------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
