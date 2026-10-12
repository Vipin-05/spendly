# Spec: Registration

## Overview
Registration allows new users to create an account on Spendly by providing their full name, email address, and a secure password. It validates submitted credentials, enforces unique email addresses, hashes passwords with Werkzeug, persists user records in SQLite, and logs the user in or redirects with confirmation. As Step 2 in the Spendly roadmap, registration enables user identity creation necessary for user-isolated authentication, profiles, and expense tracking.

## Depends on
Step 01: Database Setup (`database/db.py` with `users` schema, `get_db()` connection helper, and foreign keys enabled).

## Routes
- `GET /register` — Displays the account registration form — Public
- `POST /register` — Validates inputs, hashes password, creates user in database, redirects to `/login` — Public

## Database changes
No database changes. The `users` table was established in Step 01.
Helper functions to add to `database/db.py`:
- `create_user(name, email, password_hash)` — Inserts a new user record using parameterized SQL and returns the user ID or user dict.
- `get_user_by_email(email)` — Retrieves user record by email using parameterized SQL for uniqueness checks and authentication.

## Templates
- **Create:** None
- **Modify:** `templates/register.html` — Use `url_for('register')` for form action, render error message when present, and preserve submitted `name` and `email` values on validation error.

## Files to change
- `database/db.py` — Add `create_user` and `get_user_by_email` functions using parameterized queries.
- `app.py` — Set `app.secret_key`, update `register` route to handle `POST` requests, validate form data, invoke DB helpers, and redirect.
- `templates/register.html` — Update form action to `{{ url_for('register') }}`, display error alert, and retain input values on failure.

## Files to create
- `tests/test_register.py` — Automated tests covering successful registration, validation errors, duplicate email prevention, and password hashing verification.

## New dependencies
No new dependencies. (Flask, SQLite3, Werkzeug, and Pytest are already in `requirements.txt`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders in SQL)
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs in `database/db.py` only, never inline in route functions
- Never hardcode URLs in templates — always use `url_for()`
- Single responsibility route functions: fetch data, call DB helper, render template or redirect

## Definition of done
- [ ] Visiting `GET /register` renders `register.html` with status 200
- [ ] Submitting empty fields shows a clear error message and prevents submission
- [ ] Submitting an invalid email format shows an error message
- [ ] Submitting a password with fewer than 8 characters shows a validation error
- [ ] Submitting an email that already exists displays an error without crashing
- [ ] On validation failure, previously submitted name and email values are preserved in the form
- [ ] Submitting valid data inserts a new record into `users` table with password hashed via `werkzeug.security`
- [ ] Successful registration redirects to `/login` (with a success message)
- [ ] Passwords are never stored in plain text
- [ ] All tests in `tests/test_register.py` pass when running `pytest`
