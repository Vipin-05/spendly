import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Default database location in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spendly.db")

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db(db_path=None):
    """
    Opens a SQLite connection with row_factory configured as sqlite3.Row
    and foreign keys enabled via PRAGMA foreign_keys = ON.
    """
    target_path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """
    Creates users and expenses tables using CREATE TABLE IF NOT EXISTS.
    Safe to call multiple times.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()


def seed_db(db_path=None):
    """
    Inserts demo data if the users table is empty.
    Prevents duplicate inserts on subsequent calls.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]

    if user_count > 0:
        conn.close()
        return

    # Insert demo user
    demo_password_hash = generate_password_hash("demo123")
    cursor.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?);
        """,
        ("Demo User", "demo@spendly.com", demo_password_hash),
    )
    user_id = cursor.lastrowid

    # 8 sample expenses covering all categories across current month
    today = datetime.now()
    year = today.year
    month = today.month

    sample_expenses = [
        (user_id, 45.50, "Food", f"{year:04d}-{month:02d}-01", "Grocery shopping at supermarket"),
        (user_id, 12.00, "Transport", f"{year:04d}-{month:02d}-03", "Metro card reload"),
        (user_id, 85.00, "Bills", f"{year:04d}-{month:02d}-05", "Monthly electricity bill"),
        (user_id, 30.00, "Health", f"{year:04d}-{month:02d}-08", "Pharmacy vitamins and medicine"),
        (user_id, 24.50, "Entertainment", f"{year:04d}-{month:02d}-10", "Movie tickets and popcorn"),
        (user_id, 65.99, "Shopping", f"{year:04d}-{month:02d}-12", "New pair of running shoes"),
        (user_id, 15.00, "Other", f"{year:04d}-{month:02d}-15", "Stationery and notebook"),
        (user_id, 18.75, "Food", f"{year:04d}-{month:02d}-18", "Dinner with colleagues"),
    ]

    cursor.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?);
        """,
        sample_expenses,
    )

    conn.commit()
    conn.close()
