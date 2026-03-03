from flask import Flask, render_template, request, redirect
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

app = Flask(__name__)

# PostgreSQLのURL（RenderのEnvironment Variablesで設定済み）
DATABASE_URL = os.environ.get("DATABASE_URL")

# --------------------
# DB 接続
# --------------------
def get_db():
    """データベース接続を取得"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

# --------------------
# 初回起動時にテーブル作成
# --------------------
def init_db():
    """tasksテーブルが存在しなければ作成"""
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

# アプリ起動時に必ずテーブル作成
init_db()

# --------------------
# ルート
# --------------------
@app.route("/", methods=["GET"])
def index():
    sort = request.args.get("sort", "")
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
    cur.execute(f"SELECT * FROM tasks WHERE completed = FALSE {order}")
    tasks = cur.fetchall()
    cur.execute(f"SELECT * FROM tasks WHERE completed = TRUE {order}")
    completed_tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=None)

# --------------------
# タスク追加
# --------------------
@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None
    if due_date:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, due_date) VALUES (%s, %s)", (title, due_date))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

# --------------------
# タスク完了切替
# --------------------
@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = NOT completed WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

# --------------------
# タスク編集
# --------------------
@app.route("/edit/<int:task_id>", methods=["GET"])
def edit(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    editing_task = cur.fetchone()
    cur.execute("SELECT * FROM tasks WHERE completed = FALSE")
    tasks = cur.fetchall()
    cur.execute("SELECT * FROM tasks WHERE completed = TRUE")
    completed_tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=editing_task)

@app.route("/update/<int:task_id>", methods=["POST"])
def update(task_id):
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None
    if due_date:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET title=%s, due_date=%s WHERE id=%s", (title, due_date, task_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

# --------------------
# タスク削除
# --------------------
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
