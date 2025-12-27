import os
from flask import Flask, render_template, request, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)


# --------------------
# DB 接続
# --------------------
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


# --------------------
# 初回用：テーブル作成
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
    )
    """)
    conn.commit()
    cur.close()
    conn.close()


# --------------------
# ルート
# --------------------
@app.route("/", methods=["GET"])
def index():
    conn = get_db()
    cur = conn.cursor()

    # 並び替え処理
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

    # 未完了タスク取得
    cur.execute(f"SELECT * FROM tasks WHERE completed = FALSE {order}")
    tasks = cur.fetchall()

    # 完了済みタスク取得
    cur.execute(f"SELECT * FROM tasks WHERE completed = TRUE {order}")
    completed_tasks = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=None)


# --------------------
# タスク追加
# --------------------
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, due_date) VALUES (%s, %s)", (title, due_date))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# --------------------
# タスク完了/未完了切替
# --------------------
@app.route("/complete/<int:task_id>", methods=["POST"])
def toggle_complete(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = NOT completed WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# --------------------
# タスク削除
# --------------------
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# --------------------
# タスク編集
# --------------------
@app.route("/edit/<int:task_id>", methods=["GET"])
def edit_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("index.html", editing_task=task, tasks=[], completed_tasks=[])


@app.route("/update/<int:task_id>", methods=["POST"])
def update_task(task_id):
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET title=%s, due_date=%s WHERE id=%s", (title, due_date, task_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# --------------------
# アプリ起動
# --------------------
if __name__ == "__main__":
    init_db()  # 初回デプロイ時にテーブル作成
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
