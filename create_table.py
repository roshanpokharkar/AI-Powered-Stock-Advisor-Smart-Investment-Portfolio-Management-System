import sqlite3

conn = sqlite3.connect('database.db')

# users table
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT,
    password TEXT
)
""")

# recommendations table  ✅ ADD THIS
conn.execute("""
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    income INTEGER,
    risk TEXT,
    duration TEXT,
    goal TEXT,
    recommendation TEXT,
    created_at TEXT
)
""")

conn.commit()
conn.close()

print("Tables created successfully")
