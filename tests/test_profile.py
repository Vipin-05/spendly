import pytest
from flask import session
from app import app
from database.db import (
    init_db,
    seed_db,
    get_user_by_id,
    create_user,
    update_user_name,
    get_user_expense_stats,
    get_user_category_expenses,
)


@pytest.fixture
def test_env(tmp_path):
    """Sets up an isolated test database and configured Flask test client."""
    db_file = str(tmp_path / "test_spendly.db")
    app.config["DATABASE"] = db_file
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    init_db(db_file)
    seed_db(db_file)

    with app.test_client() as client:
        yield client, db_file


def test_profile_unauthenticated_redirect(test_env):
    """GET /profile when not logged in redirects to /login with flash message."""
    client, _ = test_env
    res = client.get("/profile", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["Location"] == "/login"

    follow_res = client.get(res.headers["Location"])
    assert follow_res.status_code == 200
    html = follow_res.get_data(as_text=True)
    assert "Please sign in to access your profile." in html


def test_profile_authenticated_page_renders(test_env):
    """GET /profile for authenticated user displays profile dashboard with user info and stats."""
    client, db_file = test_env

    # Log in as demo user
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    res = client.get("/profile")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Verify user details
    assert "Demo User" in html
    assert "demo@spendly.com" in html
    assert "Active Member" in html
    assert "Personal Information" in html
    assert 'action="/profile"' in html

    # Verify seeded expenses stats (Demo User has 8 seeded expenses)
    stats = get_user_expense_stats(1, db_file)
    assert stats["count"] == 8
    assert f"{stats['count']}" in html
    assert "₹296.74" in html

    # Verify category spending breakdown table and horizontal bars
    assert "Category Spending" in html
    assert "Spending Distribution" in html
    assert "Food" in html
    assert "Bills" in html
    assert "category-bar-fill" in html


def test_profile_update_name_success(test_env):
    """POST /profile with valid name updates DB and session, flashing success."""
    client, db_file = test_env

    # Log in as demo user
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    res = client.post(
        "/profile",
        data={"name": "Alex Mercer"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "/profile"

    # Verify session update
    with client.session_transaction() as sess:
        assert sess.get("user_name") == "Alex Mercer"

    # Verify DB update
    updated_user = get_user_by_id(1, db_file)
    assert updated_user["name"] == "Alex Mercer"

    # Follow redirect and verify updated content and toast
    follow_res = client.get(res.headers["Location"])
    assert follow_res.status_code == 200
    html = follow_res.get_data(as_text=True)
    assert "Profile updated successfully!" in html
    assert "Alex Mercer" in html


def test_profile_update_empty_name_error(test_env):
    """POST /profile with empty or whitespace name displays validation error and does not update DB."""
    client, db_file = test_env

    # Log in as demo user
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    res = client.post(
        "/profile",
        data={"name": "   "},
        follow_redirects=False,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Full name cannot be empty." in html

    # Verify DB was NOT updated
    user = get_user_by_id(1, db_file)
    assert user["name"] == "Demo User"


def test_profile_stale_session_redirects(test_env):
    """Accessing /profile with an invalid/stale user_id in session clears session and redirects to /login."""
    client, _ = test_env

    with client.session_transaction() as sess:
        sess["user_id"] = 99999
        sess["user_name"] = "Ghost User"

    res = client.get("/profile", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["Location"] == "/login"

    # Session must be cleared
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

    follow_res = client.get(res.headers["Location"])
    assert follow_res.status_code == 200
    assert "User account not found. Please sign in again." in follow_res.get_data(as_text=True)


def test_db_update_user_name_helper(test_env):
    """Unit test for update_user_name helper in database/db.py."""
    _, db_file = test_env

    # Valid update
    success = update_user_name(1, "Updated User", db_file)
    assert success is True
    user = get_user_by_id(1, db_file)
    assert user["name"] == "Updated User"

    # Empty name should fail
    fail = update_user_name(1, "   ", db_file)
    assert fail is False

    # Non-existent user
    non_existent = update_user_name(99999, "Nobody", db_file)
    assert non_existent is False


def test_db_get_user_expense_stats_helper(test_env):
    """Unit test for get_user_expense_stats helper in database/db.py."""
    _, db_file = test_env

    # Seeded user (user_id = 1) has 8 expenses
    stats = get_user_expense_stats(1, db_file)
    assert stats["count"] == 8
    assert round(stats["total_spent"], 2) == 296.74

    # Non-existent user should return 0 count and 0.0 total
    empty_stats = get_user_expense_stats(9999, db_file)
    assert empty_stats["count"] == 0
    assert empty_stats["total_spent"] == 0.0


def test_db_get_user_category_expenses_helper(test_env):
    """Unit test for get_user_category_expenses helper in database/db.py."""
    _, db_file = test_env

    # Seeded user (user_id = 1) has 8 expenses across 7 categories
    cat_expenses = get_user_category_expenses(1, db_file)
    assert len(cat_expenses) == 7

    # Verify ordered descending by total_amount
    amounts = [c["total_amount"] for c in cat_expenses]
    assert amounts == sorted(amounts, reverse=True)

    # Bills was 85.00 (highest single item)
    assert cat_expenses[0]["category"] == "Bills"
    assert cat_expenses[0]["total_amount"] == 85.0
    assert cat_expenses[0]["count"] == 1

    # Verify percentages sum approximately to 100%
    total_pct = sum(c["percentage"] for c in cat_expenses)
    assert 99.0 <= total_pct <= 101.0

    # Non-existent user returns empty list
    empty_list = get_user_category_expenses(9999, db_file)
    assert empty_list == []


def test_profile_category_expenses_empty_state(test_env):
    """Profile page for a user with 0 expenses displays clean empty state message."""
    client, db_file = test_env

    # Create a fresh user with no expenses
    new_user_id = create_user("Zero Expenses User", "zero@example.com", "dummyhash", db_file)

    # Establish session
    with client.session_transaction() as sess:
        sess["user_id"] = new_user_id
        sess["user_name"] = "Zero Expenses User"

    res = client.get("/profile")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Verify empty state rendered
    assert "No expenses recorded yet" in html
    assert "Your category breakdown will appear here once you log your first expenses." in html
    assert "Spending Distribution" not in html
