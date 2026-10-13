# Spec: Login and Logout

## Overview
Login and logout functionality enables existing Spendly users to authenticate with their credentials, establish a persistent server-side cookie session, access user-specific pages, and cleanly terminate their authenticated session. Step 3 in the Spendly roadmap provides the security and session boundary required to protect user profiles and expense management routes, updating navigation states dynamically across the application based on authentication status.

## Depends on
- Step 01: Database Setup (`database/db.py` SQLite schema, `get_db()` connection helper, and initialized `users` table).
- Step 02: Registration (`database/db.py` user records with hashed passwords and `get_user_by_email` lookup function).

## Routes
- `GET /login` — Displays the login form (redirects authenticated users if session is active) — Public
- `POST /login` — Validates submitted credentials, verifies password hash, stores user identity in Flask `session`, flashes feedback, and redirects to landing or profile — Public
- `GET /logout` — Clears user session data, flashes a logout confirmation message, and redirects to login or landing page — Logged-in / Public

## Database changes
No database changes. The `users` table established in Step 01 contains all necessary fields (`id`, `name`, `email`, `password_hash`).
Helper functions in `database/db.py`:
- `get_user_by_email(email)` is already implemented and used to fetch existing user records.
- Optional helper: `get_user_by_id(user_id)` to retrieve user details from session stored id if needed.

## Templates
- **Create:** None
- **Modify:**
  - `templates/login.html` — Ensure form submits via `POST` to `{{ url_for('login') }}`, renders flash messages, retains `email` field on failed attempts, and shows error messages when credentials fail.
  - `templates/base.html` — Update navigation bar links dynamically according to `session.get('user_id')`:
    - When authenticated: show user greeting/profile link and "Sign out" (`url_for('logout')`).
    - When unauthenticated: show "Sign in" (`url_for('login')`) and "Get started" (`url_for('register')`).

## Files to change
- `app.py` — Update `login` route to handle `POST` method, authenticate credentials via `check_password_hash`, set session keys (`user_id`, `user_name`), implement `logout` route to clear `session` and redirect to `url_for('login')`.
- `templates/login.html` — Ensure proper display of errors, flashed messages, and preservation of email input on error.
- `templates/base.html` — Conditional rendering in navbar based on session authentication state (`user_id` in session).

## Files to create
- `tests/test_auth.py` — Automated tests covering login form rendering, valid login, invalid login (wrong password, non-existent email), empty input validation, session persistence, logout session termination, and navbar authentication state changes.

## New dependencies
No new dependencies. (Flask, SQLite3, Werkzeug, and Pytest are already in `requirements.txt`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed and verified with werkzeug (`check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs in `database/db.py` only, never inline in routes
- Never hardcode URLs in templates — always use `url_for()`
- Use Flask's `session` object to manage user login state
- Never use raw string returns for implemented routes — always render a template or redirect

## Definition of done
- [ ] Visiting `GET /login` displays `login.html` with status 200
- [ ] Submitting empty email or password displays an appropriate error message
- [ ] Submitting non-existent email displays an invalid credentials error message
- [ ] Submitting incorrect password displays an invalid credentials error message
- [ ] Submitting valid credentials sets `session['user_id']` and redirects to landing page or profile
- [ ] On failed login attempt, the submitted email is preserved in the form input
- [ ] Navbar dynamically renders authenticated links ("Sign out") when logged in and unauthenticated links ("Sign in", "Get started") when logged out
- [ ] Visiting `GET /logout` clears user session, displays flash confirmation message, and redirects to `/login`
- [ ] Logged-out users cannot access active session state
- [ ] All tests in `tests/test_auth.py` pass with `pytest`
