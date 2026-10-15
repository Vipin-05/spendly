# Spec: Profile Page

## Overview
The Profile Page provides authenticated Spendly users with a centralized account management dashboard where they can view their profile details, monitor their expense tracking activity summary, view a category-wise spending breakdown with horizontal visualizer bars, and update their personal information (such as display name). Step 4 bridges authentication and expense management by giving logged-in users a dedicated personal space, enforcing session-based access controls, immediately welcoming them upon login, and visually reflecting user identity across the application.

## Depends on
- Step 01: Database Setup (`database/db.py` SQLite schema, `get_db()` helper, and `users` and `expenses` tables).
- Step 02: Registration (`database/db.py` user creation and password hashing).
- Step 03: Login and Logout (`app.py` authentication flow, `session` state, and navbar navigation).

## Routes
- `GET /profile` — Displays the user profile page with account details, overall stats, and category-wise spending visualizer table — Logged-in only
- `POST /profile` — Validates and updates user profile information (display name) — Logged-in only
- `POST /login` — Authenticates user, establishes session, and redirects directly to `url_for('profile')` without toast message — Public

## Database changes
No schema alterations are needed. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) and `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) contain all required data.

Helper functions in `database/db.py`:
- `update_user_name(user_id, new_name, db_path=None)`: Parameterized update for `users.name`.
- `get_user_expense_stats(user_id, db_path=None)`: Parameterized query calculating total expense count and total spent for the user.
- `get_user_category_expenses(user_id, db_path=None)`: Parameterized query aggregating expenses by category (count, total_amount, percentage share).

## Templates
- **Create / Update:**
  - `templates/profile.html` — Full profile dashboard extending `base.html`, featuring:
    - User avatar monogram, badge, and header.
    - Top stats cards (count, total spending, member since).
    - Category-wise expense breakdown table with horizontal distribution bars.
    - Personal information update form.
- **Modify:** None (`base.html` already links to `url_for('profile')` when logged in).

## Files to change
- `app.py` — Update login redirect to `/profile` (removing welcome toast), and wire `category_expenses` to `/profile`.
- `database/db.py` — Implement `get_user_category_expenses` helper.
- `templates/profile.html` — Render category breakdown table and horizontal bars.
- `static/css/profile.css` — Styles for category table and horizontal progress bars.
- `tests/test_auth.py` — Update login assertions for `/profile` redirect and removal of welcome message.
- `tests/test_profile.py` — Add tests for category breakdown, empty state, and helper function.

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
- [ ] Successful login redirects to `url_for('profile')` directly without a "Welcome back" flash toast
- [ ] Visiting `GET /profile` while unauthenticated redirects to `url_for('login')` with an error message
- [ ] Visiting `GET /profile` while logged in displays `profile.html` with status 200
- [ ] Page renders user name, email, member since date, monogram avatar, and expense summary stats
- [ ] Category-wise expenses table displays category name, transaction count, total currency amount, and horizontal distribution bars with percentages
- [ ] Empty state renders gracefully when a user has no recorded expenses
- [ ] Submitting empty/blank name on `POST /profile` shows a validation error and preserves state without updating DB
- [ ] Submitting a valid new name on `POST /profile` updates `users.name` in DB, updates `session['user_name']`, flashes a success message, and redirects to `/profile`
- [ ] Navbar display name immediately reflects the updated user name
- [ ] Stale or invalid session IDs redirect safely to `/login` with cleared session
- [ ] All tests in `tests/test_auth.py` and `tests/test_profile.py` pass with `pytest`
