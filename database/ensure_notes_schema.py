#!/usr/bin/env python3
"""Ensure the SQLite notes schema exists.

This helper is intentionally minimal and idempotent:
- Reads the authoritative SQLite DB file path from db_connection.txt.
- Applies required DDL statements one at a time.
- Safe to run repeatedly.

Usage:
  python3 ensure_notes_schema.py
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys


def _get_db_path_from_connection_file(connection_file: str = "db_connection.txt") -> str:
    """Return the authoritative SQLite file path from db_connection.txt (fallback: myapp.db)."""
    default = "myapp.db"
    if not os.path.exists(connection_file):
        return default

    with open(connection_file, "r", encoding="utf-8") as f:
        text = f.read()

    m = re.search(r"^\s*#\s*File path:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return m.group(1).strip() if m else default


# PUBLIC_INTERFACE
def ensure_notes_schema(db_path: str) -> None:
    """Create/upgrade the `notes` table to the expected minimal schema.

    Args:
        db_path: Path to the SQLite database file.

    Raises:
        sqlite3.Error: If a database error occurs.
    """
    ddl_statements = [
        # Create notes table if it doesn't exist, per specification.
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """.strip()
    ]

    # Single-statement execution: apply each DDL statement individually.
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        for ddl in ddl_statements:
            cur.execute(ddl)
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    """Entrypoint for the schema helper."""
    db_path = _get_db_path_from_connection_file()
    print(f"Using SQLite DB: {db_path}")
    try:
        ensure_notes_schema(db_path)
        print("✓ notes schema ensured")
    except sqlite3.Error as e:
        print(f"✗ failed to ensure notes schema: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
