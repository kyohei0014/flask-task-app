from flask import Flask, render_template, request, redirect, flash
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret-key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = ""

# PostgreSQLのURL（RenderのEnvironment Variablesで設定済み）
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set!")

# postgres:// を postgresql:// に変換
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("Using DB:", DATABASE_URL)

# --------------------
# DB 接続
# --------------------
def get_db():
    """データベース接続を取得"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

# --------------------
# Userクラス
# --------------------
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

login_manager.login_view = "login"

# --------------------
# 初回起動時にテーブル作成
# --------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # users テーブル
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    """)

    # tasks テーブル
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        completed BOOLEAN DEFAULT FALSE
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
# アプリ起動時に必ずテーブル作成
init_db()
@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, username FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if user:
        return User(user["id"], user["username"])
    return None

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash),
        )

        conn.commit()
        cur.close()
        conn.close()
        flash("ユーザー登録が完了しました")
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username=%s",
            (username,),
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            login_user(User(user["id"], user["username"]))
            return redirect("/")
        flash("ユーザー名またはパスワードが違います")
    return render_template("login.html")

# --------------------
# ログアウト
# --------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました")
    return redirect("/login")

# --------------------
# ルート
# --------------------
@app.route("/", methods=["GET"])
@login_required
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
    cur.execute(
        f"SELECT * FROM tasks WHERE user_id=%s AND completed = FALSE {order}",
        (current_user.id,)
    )
    tasks = cur.fetchall()
    cur.execute(
        f"SELECT * FROM tasks WHERE user_id=%s AND completed = TRUE {order}",
        (current_user.id,)
    )
    completed_tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=None)

# --------------------
# タスク追加
# --------------------
@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title")
    due_date = request.form.get("due_date") or None
    if due_date:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, title, due_date) VALUES (%s, %s, %s)",
        (current_user.id, title, due_date)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

# --------------------
# タスク完了切替
# --------------------
@app.route("/complete/<int:task_id>", methods=["POST"])
@login_required
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
@login_required
def edit(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE id=%s AND user_id=%s",
        (task_id, current_user.id)
    )
    editing_task = cur.fetchone()
    cur.execute(
        "SELECT * FROM tasks WHERE user_id=%s AND completed=FALSE",
        (current_user.id,)
    )
    tasks = cur.fetchall()
    cur.execute(
        "SELECT * FROM tasks WHERE user_id=%s AND completed=TRUE",
        (current_user.id,)
    )
    completed_tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", tasks=tasks, completed_tasks=completed_tasks, editing_task=editing_task)

@app.route("/update/<int:task_id>", methods=["POST"])
@login_required
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
@login_required
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
