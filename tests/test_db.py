import os
import sqlite3
import pytest
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, CATEGORIES


@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture providing a temporary SQLite database path."""
    return str(tmp_path / "test_spendly.db")


def test_get_db(temp_db_path):
    conn = get_db(temp_db_path)
    try:
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row

        # Verify PRAGMA foreign_keys is enabled
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        fk_enabled = cursor.fetchone()[0]
        assert fk_enabled == 1
    finally:
        conn.close()


def test_init_db(temp_db_path):
    init_db(temp_db_path)

    conn = get_db(temp_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        assert "users" in tables
        assert "expenses" in tables

        # Re-running init_db should be idempotent and not raise errors
        init_db(temp_db_path)
    finally:
        conn.close()


def test_seed_db(temp_db_path):
    init_db(temp_db_path)
    seed_db(temp_db_path)

    conn = get_db(temp_db_path)
    try:
        cursor = conn.cursor()

        # Check demo user
        cursor.execute("SELECT * FROM users;")
        users = cursor.fetchall()
        assert len(users) == 1
        user = users[0]
        assert user["name"] == "Demo User"
        assert user["email"] == "demo@spendly.com"
        assert check_password_hash(user["password_hash"], "demo123")

        # Check expenses
        cursor.execute("SELECT * FROM expenses;")
        expenses = cursor.fetchall()
        assert len(expenses) == 8

        # Check all categories represented
        expense_categories = {exp["category"] for exp in expenses}
        for cat in CATEGORIES:
            assert cat in expense_categories

        # Check all expenses linked to demo user
        for exp in expenses:
            assert exp["user_id"] == user["id"]
            assert isinstance(exp["amount"], float)
            assert len(exp["date"].split("-")) == 3

        # Calling seed_db again must not duplicate data
        seed_db(temp_db_path)
        cursor.execute("SELECT COUNT(*) FROM users;")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM expenses;")
        assert cursor.fetchone()[0] == 8
    finally:
        conn.close()


def test_unique_email_constraint(temp_db_path):
    init_db(temp_db_path)
    seed_db(temp_db_path)

    conn = get_db(temp_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);",
                ("Duplicate", "demo@spendly.com", "hash123"),
            )
            conn.commit()
    finally:
        conn.close()


def test_foreign_key_constraint(temp_db_path):
    init_db(temp_db_path)

    conn = get_db(temp_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?);
                """,
                (99999, 10.0, "Food", "2026-10-06", "Non-existent user"),
            )
            conn.commit()
    finally:
        conn.close()
