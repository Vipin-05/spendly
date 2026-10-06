# Implementation Plan - Step 1: Database Setup

## Goal Description
Implement the core data persistence layer for Spendly in `database/db.py` and hook it into `app.py` on startup. This sets up the SQLite schema for users and expenses, ensures foreign key enforcement and dict-like row access, and safely populates seed data (demo user and 8 categorized expenses) without duplication on subsequent runs.

---

## User Review Required
> [!NOTE]
> Database file location defaults to `spendly.db` at the project root (`os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spendly.db')`). Helper functions will accept an optional `db_path` parameter to make unit testing with temporary or in-memory databases straightforward and clean.

> [!IMPORTANT]
> `PRAGMA foreign_keys = ON;` is executed on every SQLite connection because SQLite defaults foreign key constraints to OFF.

---

## Open Questions
None. All schema definitions, constraints, categories, and seed data specifications are fully outlined in `.agents/specs/01-database-setup.md`.

---

## Proposed Changes

### Database Layer (`database/`)

#### [MODIFY] [database/db.py](file:///Users/vipinchaudhari/Downloads/expense-tracker/database/db.py)
Replace the existing comments and stubs with complete implementations of `get_db()`, `init_db()`, and `seed_db()`.

- **Imports**: `sqlite3`, `os`, `datetime`, and `generate_password_hash` from `werkzeug.security`.
- **Constants**:
  - `DB_PATH`: Absolute path to `spendly.db` at the project root.
  - `CATEGORIES`: `['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']`.
- **`get_db(db_path=None)`**:
  - Connects to `db_path or DB_PATH`.
  - Sets `conn.row_factory = sqlite3.Row`.
  - Runs `conn.execute("PRAGMA foreign_keys = ON;")`.
  - Returns connection.
- **`init_db(db_path=None)`**:
  - Opens connection via `get_db(db_path)`.
  - Creates `users` table:
    ```sql
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    ```
  - Creates `expenses` table:
    ```sql
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
    ```
  - Commits changes and closes connection.
- **`seed_db(db_path=None)`**:
  - Queries `SELECT COUNT(*) FROM users;`.
  - If count > 0, returns immediately (no duplicate seeding).
  - Inserts demo user:
    - Name: `Demo User`
    - Email: `demo@spendly.com`
    - Password: `demo123` hashed via `generate_password_hash('demo123')`
  - Retrieves created demo user `id`.
  - Inserts 8 sample expenses for the demo user:
    - Spanning categories: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other` (ensuring at least 1 for each of the 7 categories + 1 additional Food expense to total 8).
    - Dates formatted as `YYYY-MM-DD` within the current month.
    - Amounts as `REAL` (floats).
  - Commits changes and closes connection.

---

### Application Entry Point

#### [MODIFY] [app.py](file:///Users/vipinchaudhari/Downloads/expense-tracker/app.py)
- Import `init_db`, `seed_db` from `database.db`.
- Initialize database on application startup within `with app.app_context():`:
  ```python
  with app.app_context():
      init_db()
      seed_db()
  ```
- Leave all existing and placeholder routes unchanged as specified.

---

### Automated Tests (`tests/`)

#### [NEW] [tests/test_db.py](file:///Users/vipinchaudhari/Downloads/expense-tracker/tests/test_db.py)
Create test suite to verify:
1. `test_get_db`: Returns SQLite connection with `sqlite3.Row` factory and foreign keys enabled.
2. `test_init_db`: Idempotently creates `users` and `expenses` tables.
3. `test_seed_db`: Inserts demo user and exactly 8 expenses covering all 7 categories; calling `seed_db()` twice does not duplicate records.
4. `test_unique_email_constraint`: Inserting user with duplicate email raises `sqlite3.IntegrityError`.
5. `test_foreign_key_constraint`: Inserting expense with nonexistent `user_id` raises `sqlite3.IntegrityError`.

---

## Verification Plan

### Automated Tests
Run pytest via terminal:
```bash
pytest -v tests/test_db.py
```
And verify full test suite:
```bash
pytest
```

### Manual Verification
1. Run app startup:
   ```bash
   python -c "from app import app; print('App initialized successfully')"
   ```
2. Inspect `spendly.db` created in project root:
   ```bash
   sqlite3 spendly.db "SELECT id, name, email FROM users;"
   sqlite3 spendly.db "SELECT id, amount, category, date, description FROM expenses;"
   ```
3. Run startup command again and verify user and expense count remains 1 user and 8 expenses.
