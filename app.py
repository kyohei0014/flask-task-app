from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# --------------------
# DB 接続
# --------------------
def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

# --------------------
# DB 初期化
# --------------------
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT,
            due_date TEXT
        )
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
    completed_query = base_query + " WHERE completed = 1"
    uncompleted_query = base_query + " WHERE completed = 0"

    # 並び替え
    if sort == "created_new":
        order = " ORDER BY datetime(created_at) DESC"
    elif sort == "created_old":
        order = " ORDER BY datetime(created_at) ASC"
    elif sort == "due_near":
        order = " ORDER BY datetime(due_date) ASC"
    elif sort == "due_far":
        order = " ORDER BY datetime(due_date) DESC"
    else:
        order = ""

    conn = get_db()
    uncompleted = conn.execute(uncompleted_query + order).fetchall()
    completed = conn.execute(completed_query + order).fetchall()
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
    conn.execute("""
        INSERT INTO tasks (title, created_at, due_date, completed)
        VALUES (?, datetime('now','localtime'), ?, 0)
    """, (title, due_date))
    conn.commit()
    conn.close()

    return redirect("/")



# --------------------
# 削除
# --------------------
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
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

    # 今の状態取得
    cur.execute("SELECT completed FROM tasks WHERE id=?", (task_id,))
    current = cur.fetchone()

    if current is not None:
        new_value = 0 if current["completed"] == 1 else 1
        cur.execute("UPDATE tasks SET completed=? WHERE id=?", (new_value, task_id))
        conn.commit()

    conn.close()
    return redirect("/")



# --------------------
# 編集（同じ画面で表示）
# --------------------
@app.route("/edit/<int:task_id>")
def edit(task_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, title, completed FROM tasks WHERE completed = 0")
    tasks = cur.fetchall()

    cur.execute("SELECT id, title, completed FROM tasks WHERE completed = 1")
    completed_tasks = cur.fetchall()

    cur.execute("SELECT id, title, completed FROM tasks WHERE id=?", (task_id,))
    editing_task = cur.fetchone()

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
    new_due_date = request.form.get("due_date", "").strip()  # 期限を取得

    if not new_title:
        return redirect(f"/edit/{task_id}")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title=?, due_date=? WHERE id=?",
        (new_title, new_due_date if new_due_date else None, task_id)
    )
    conn.commit()
    conn.close()

    return redirect("/")





# --------------------
# 起動
# --------------------
# アプリ起動時に必ずDB初期化
init_db()

if __name__ == "__main__":
    app.run()

