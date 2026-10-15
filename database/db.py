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
    if db_path is not None:
        target_path = db_path
    else:
        try:
            from flask import current_app
            target_path = current_app.config.get("DATABASE", DB_PATH)
        except Exception:
            target_path = DB_PATH
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


def get_user_by_email(email, db_path=None):
    """
    Fetches a user record by email (case-insensitive).
    Returns sqlite3.Row if found, otherwise None.
    """
    normalized_email = email.strip().lower() if email else ""
    conn = get_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?;", (normalized_email,))
        return cursor.fetchone()
    finally:
        conn.close()


def create_user(name, email, password_hash, db_path=None):
    """
    Inserts a new user record into the users table using parameterized SQL.
    Returns the newly created user's integer id.
    """
    normalized_name = name.strip() if name else ""
    normalized_email = email.strip().lower() if email else ""
    conn = get_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?);
            """,
            (normalized_name, normalized_email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_id(user_id, db_path=None):
    """
    Fetches a user record by primary key id.
    Returns sqlite3.Row if found, otherwise None.
    """
    conn = get_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def update_user_name(user_id, new_name, db_path=None):
    """
    Updates the user's display name in the users table using parameterized SQL.
    Returns True if update succeeded, False otherwise.
    """
    normalized_name = new_name.strip() if new_name else ""
    if not normalized_name:
        return False
    conn = get_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET name = ?
            WHERE id = ?;
            """,
            (normalized_name, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_user_expense_stats(user_id, db_path=None):
    """
    Returns summary statistics for the user's expenses:
    count: total number of expenses
    total_spent: sum of amounts (float)
    """
    conn = get_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0.0) AS total_spent
            FROM expenses
            WHERE user_id = ?;
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return {
            "count": row["count"] if row else 0,
            "total_spent": float(row["total_spent"]) if row else 0.0,
        }
    finally:
        conn.close()


def get_user_category_expenses(user_id, db_path=None):
    """
    Returns category-wise spending breakdown for a user, ordered by total spent descending.
    Each item contains:
      - category: str
      - count: int
      - total_amount: float (rounded to 2 decimal places)
      - percentage: float (relative share of user's overall spending 0.0 - 100.0)
    """
    conn = get_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, COUNT(*) AS count, COALESCE(SUM(amount), 0.0) AS total_amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total_amount DESC;
            """,
            (user_id,),
        )
        rows = cursor.fetchall()

        overall_total = sum(float(r["total_amount"]) for r in rows)

        results = []
        for r in rows:
            amount = round(float(r["total_amount"]), 2)
            pct = round((amount / overall_total * 100.0), 1) if overall_total > 0 else 0.0
            results.append({
                "category": r["category"],
                "count": r["count"],
                "total_amount": amount,
                "percentage": pct,
            })
        return results
    finally:
        conn.close()

