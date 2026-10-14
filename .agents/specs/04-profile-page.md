# Spec: Profile Page

## Overview
The Profile Page provides authenticated Spendly users with a centralized account management dashboard where they can view their profile details, monitor their expense tracking activity summary, and update their personal information (such as display name). Step 4 bridges authentication and expense management by giving logged-in users a dedicated personal space, enforcing session-based access controls, and visually reflecting user identity across the application.

## Depends on
- Step 01: Database Setup (`database/db.py` SQLite schema, `get_db()` helper, and `users` and `expenses` tables).
- Step 02: Registration (`database/db.py` user creation and password hashing).
- Step 03: Login and Logout (`app.py` authentication flow, `session` state, and navbar navigation).

## Routes
- `GET /profile` — Displays the user profile page with account details and expense stats — Logged-in only
- `POST /profile` — Validates and updates user profile information (display name) — Logged-in only

## Database changes
No schema alterations are needed. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) and `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) contain all required data.

Helper functions to add in `database/db.py`:
- `update_user_name(user_id, new_name, db_path=None)`: Parameterized update for `users.name`.
- `get_user_expense_stats(user_id, db_path=None)`: Parameterized query calculating total expense count and total spent for the user.

## Templates
- **Create:**
  - `templates/profile.html` — Full profile dashboard extending `base.html`.
- **Modify:** None (`base.html` already links to `url_for('profile')` when logged in).

## Files to change
- `app.py` — Replace `/profile` placeholder route with `GET` and `POST` handlers, authentication protection, form validation, and session synchronization.
- `database/db.py` — Implement `update_user_name` and `get_user_expense_stats`.
- `AGENTS.md` — Update route status table for Step 4.

## Files to create
- `static/css/profile.css` — Modern fintech profile page styling following `frontend-design` skill.
- `templates/profile.html` — Profile dashboard template.
- `tests/test_profile.py` — Automated tests covering authentication guards, profile viewing, profile editing, validation, and database helpers.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs in `database/db.py` only, never inline in routes
- Never hardcode URLs in templates — always use `url_for()`
- Use Flask's `session` object to manage user login state
- Only authenticated users can access `/profile`; unauthenticated requests redirect to `/login`
- Never use raw string returns for implemented routes — always render a template or redirect

## Definition of done
- [ ] Visiting `GET /profile` while unauthenticated redirects to `url_for('login')` with an error message
- [ ] Visiting `GET /profile` while logged in displays `profile.html` with status 200
- [ ] Page renders user name, email, member since date, monogram avatar, and expense summary stats
- [ ] Submitting empty/blank name on `POST /profile` shows a validation error and preserves state without updating DB
- [ ] Submitting a valid new name on `POST /profile` updates `users.name` in DB, updates `session['user_name']`, flashes a success message, and redirects to `/profile`
- [ ] Navbar display name immediately reflects the updated user name
- [ ] Stale or invalid session IDs redirect safely to `/login` with cleared session
- [ ] All tests in `tests/test_profile.py` pass with `pytest`
