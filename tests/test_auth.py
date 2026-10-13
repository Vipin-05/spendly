import sqlite3
import pytest
from flask import session
from app import app
from database.db import init_db, seed_db, get_db, create_user, get_user_by_email, get_user_by_id


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


def test_login_page_renders(test_env):
    """GET /login displays the sign-in form with email and password inputs."""
    client, _ = test_env
    response = client.get("/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'action="/login"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html
    assert "Sign in" in html
    assert "Welcome back" in html


def test_login_missing_fields(test_env):
    """POST /login with missing email or password renders error."""
    client, _ = test_env

    # Missing email
    res = client.post("/login", data={"email": "", "password": "anypassword"})
    assert res.status_code == 200
    assert "All fields are required." in res.get_data(as_text=True)

    # Missing password
    res = client.post("/login", data={"email": "demo@spendly.com", "password": "   "})
    assert res.status_code == 200
    assert "All fields are required." in res.get_data(as_text=True)


def test_login_nonexistent_email(test_env):
    """POST /login with an email not in database displays invalid credentials error and preserves email."""
    client, _ = test_env
    res = client.post(
        "/login",
        data={"email": "unknown@example.com", "password": "somepassword"},
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Invalid email or password." in html
    assert 'value="unknown@example.com"' in html


def test_login_wrong_password(test_env):
    """POST /login with incorrect password displays error and preserves email."""
    client, _ = test_env
    res = client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "wrongpassword123"},
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Invalid email or password." in html
    assert 'value="demo@spendly.com"' in html
    assert "wrongpassword123" not in html


def test_login_success(test_env):
    """POST /login with valid credentials sets session and redirects to landing page."""
    client, _ = test_env
    res = client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "/"

    # Check session variables
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("user_name") == "Demo User"

    # Follow redirect and verify welcome toast/flash
    follow_res = client.get(res.headers["Location"])
    assert follow_res.status_code == 200
    html = follow_res.get_data(as_text=True)
    assert "Welcome back, Demo User!" in html


def test_login_case_insensitive_email(test_env):
    """POST /login handles uppercase email correctly."""
    client, _ = test_env
    res = client.post(
        "/login",
        data={"email": "DEMO@SPENDLY.COM", "password": "demo123"},
    )
    assert res.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("user_name") == "Demo User"


def test_login_already_authenticated_redirect(test_env):
    """GET /login redirects already authenticated user to landing page."""
    client, _ = test_env
    # Perform login first
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Attempt to visit /login again
    res = client.get("/login")
    assert res.status_code == 302
    assert res.headers["Location"] == "/"


def test_register_already_authenticated_redirect(test_env):
    """GET /register redirects already authenticated user to landing page."""
    client, _ = test_env
    # Perform login first
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Attempt to visit /register
    res = client.get("/register")
    assert res.status_code == 302
    assert res.headers["Location"] == "/"


def test_navbar_unauthenticated(test_env):
    """Navbar on / renders Sign in and Get started when no user session is active."""
    client, _ = test_env
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Sign in" in html
    assert "Get started" in html
    assert "Sign out" not in html


def test_navbar_authenticated(test_env):
    """Navbar on / renders user name/profile link and Sign out when user session is active."""
    client, _ = test_env
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Sign out" in html
    assert "Demo User" in html
    assert "Sign in" not in html


def test_logout_flow(test_env):
    """GET /logout clears session, flashes confirmation, and redirects to /login."""
    client, _ = test_env
    # Login first
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None

    # Visit /logout
    res = client.get("/logout")
    assert res.status_code == 302
    assert res.headers["Location"] == "/login"

    # Verify session cleared
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None
        assert sess.get("user_name") is None

    # Follow redirect and verify flash message
    follow_res = client.get(res.headers["Location"])
    assert follow_res.status_code == 200
    assert "You have been signed out." in follow_res.get_data(as_text=True)


def test_get_user_by_id_helper(tmp_path):
    """Unit test for database/db.py get_user_by_id helper function."""
    db_file = str(tmp_path / "helper_id_test.db")
    init_db(db_file)
    seed_db(db_file)

    # Demo user seeded with id=1
    user = get_user_by_id(1, db_file)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"

    # Non-existent user id returns None
    assert get_user_by_id(9999, db_file) is None
