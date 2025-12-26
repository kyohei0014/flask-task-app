import sqlite3

conn = sqlite3.connect("tasks.db")
cur = conn.cursor()

# created_at
try:
    cur.execute("ALTER TABLE tasks ADD COLUMN created_at TEXT")
except:
    pass

# due_date
try:
    cur.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
except:
    pass

conn.commit()
conn.close()

print("Migration OK")
