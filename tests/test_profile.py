import pytest
from flask import session
from app import app
from database.db import (
    init_db,
    seed_db,
    get_user_by_id,
    update_user_name,
    get_user_expense_stats,
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
