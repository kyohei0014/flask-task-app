import sqlite3

conn = sqlite3.connect("tasks.db")
cur = conn.cursor()

cur.execute("""
UPDATE tasks
SET created_at = datetime('now','localtime')
WHERE created_at IS NULL
""")

conn.commit()
conn.close()
