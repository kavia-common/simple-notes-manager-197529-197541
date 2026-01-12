#!/usr/bin/env python3
"""Initialize SQLite database for database.

This script creates the baseline schema (and keeps it up-to-date) for the SQLite DB used by the
multi-container notes app.
"""

import os
import re
import sqlite3

DB_NAME = "myapp.db"
DB_USER = "kaviasqlite"  # Not used for SQLite, but kept for consistency
DB_PASSWORD = "kaviadefaultpassword"  # Not used for SQLite, but kept for consistency
DB_PORT = "5000"  # Not used for SQLite, but kept for consistency


def _get_db_path_from_connection_file(connection_file: str = "db_connection.txt") -> str:
    """Parse db_connection.txt and return the authoritative SQLite file path if present."""
    if not os.path.exists(connection_file):
        return DB_NAME

    try:
        with open(connection_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return DB_NAME

    # Expected line format in this repo:
    #   # File path: /absolute/path/to/myapp.db
    m = re.search(r"^\s*#\s*File path:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()

    return DB_NAME


print("Starting SQLite setup...")

db_path = _get_db_path_from_connection_file()
db_exists = os.path.exists(db_path)

if db_exists:
    print(f"SQLite database already exists at {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print(f"Creating new SQLite database at {db_path}...")

# Create database with sample tables
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create initial schema
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)

# Create a sample users table as an example
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)

# Notes table for the notes app
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
"""
)

# Insert initial data
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("project_name", "database"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("version", "0.1.0"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("author", "John Doe"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("description", ""),
)

conn.commit()

# Get database statistics
cursor.execute(
    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
)
table_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM app_info")
record_count = cursor.fetchone()[0]

conn.close()

# Save connection information to a file
db_abs_path = os.path.abspath(db_path)
connection_string = f"sqlite:////{db_abs_path.lstrip('/')}"

try:
    with open("db_connection.txt", "w", encoding="utf-8") as f:
        f.write("# SQLite connection methods:\n")
        # Keep Python example stable for local relative usage; the path line below is authoritative.
        f.write("# Python: sqlite3.connect('myapp.db')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {db_abs_path}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w", encoding="utf-8") as f:
        f.write(f'export SQLITE_DB="{db_abs_path}"\n')
    print("Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nSQLite setup complete!")
print(f"Database: {os.path.basename(db_abs_path)}")
print(f"Location: {db_abs_path}")
print("")
print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")
print("\nTo connect to the database, use one of the following methods:")
print("1. Python: sqlite3.connect('myapp.db')  # if running from this directory")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {db_abs_path}")
print("")
print("Database statistics:")
print(f"  Tables: {table_count}")
print(f"  App info records: {record_count}")

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess

    result = subprocess.run(["which", "sqlite3"], capture_output=True, text=True)
    if result.returncode == 0:
        print("")
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {db_abs_path}")
except Exception:
    pass

print("\nScript completed successfully.")
