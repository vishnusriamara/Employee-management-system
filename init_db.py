import sqlite3

conn = sqlite3.connect("notes.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT,
    role TEXT,
    email TEXT,
    profile_pic TEXT
)
""")

# EMPLOYEE TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS employee (
    eid INTEGER PRIMARY KEY,
    ename TEXT,
    edept TEXT,
    esalary INTEGER,
    ephone TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")