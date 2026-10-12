import sqlite3
import pytest
from werkzeug.security import check_password_hash
from app import app
from database.db import init_db, seed_db, get_db, create_user, get_user_by_email


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


def test_register_page_get(test_env):
    client, _ = test_env
    response = client.get("/register")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'action="/register"' in html
    assert 'name="name"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html
    assert "Create your account" in html


def test_register_missing_fields(test_env):
    client, _ = test_env

    # Missing name
    res = client.post("/register", data={"name": "", "email": "new@example.com", "password": "password123"})
    assert res.status_code == 200
    assert "All fields are required." in res.get_data(as_text=True)

    # Missing email
    res = client.post("/register", data={"name": "New User", "email": "", "password": "password123"})
    assert res.status_code == 200
    assert "All fields are required." in res.get_data(as_text=True)

    # Missing password
    res = client.post("/register", data={"name": "New User", "email": "new@example.com", "password": ""})
    assert res.status_code == 200
    assert "All fields are required." in res.get_data(as_text=True)


def test_register_invalid_email_format(test_env):
    client, _ = test_env
    invalid_emails = ["notanemail", "test@", "@domain.com", "user@domain", "user name@example.com"]
    for email in invalid_emails:
        res = client.post("/register", data={"name": "New User", "email": email, "password": "password123"})
        assert res.status_code == 200
        assert "Please enter a valid email address." in res.get_data(as_text=True)


def test_register_short_password(test_env):
    client, _ = test_env
    res = client.post("/register", data={"name": "New User", "email": "valid@example.com", "password": "short"})
    assert res.status_code == 200
    assert "Password must be at least 8 characters long." in res.get_data(as_text=True)


def test_register_duplicate_email(test_env):
    client, db_file = test_env
    # demo@spendly.com is already created by seed_db
    res = client.post("/register", data={"name": "Demo Imposter", "email": "demo@spendly.com", "password": "password123"})
    assert res.status_code == 200
    assert "An account with this email already exists." in res.get_data(as_text=True)

    # Verify no duplicate was inserted in DB
    conn = get_db(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'demo@spendly.com';")
        assert cursor.fetchone()[0] == 1
    finally:
        conn.close()


def test_register_case_insensitive_duplicate_email(test_env):
    client, _ = test_env
    res = client.post("/register", data={"name": "Demo Imposter", "email": "DEMO@SPENDLY.COM", "password": "password123"})
    assert res.status_code == 200
    assert "An account with this email already exists." in res.get_data(as_text=True)


def test_register_preserves_form_inputs(test_env):
    client, _ = test_env
    res = client.post("/register", data={"name": "Preserved Name", "email": "preserved@example.com", "password": "short"})
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'value="Preserved Name"' in html
    assert 'value="preserved@example.com"' in html
    # Password should NOT be preserved in value attribute
    assert 'value="short"' not in html


def test_register_success(test_env):
    client, db_file = test_env
    res = client.post(
        "/register",
        data={"name": "Aarav Sharma", "email": "aarav.sharma@example.com", "password": "securepassword123"},
        follow_redirects=False,
    )
    # Redirects to /login
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/login")

    # Following the redirect displays success flash message
    follow_res = client.get(res.headers["Location"])
    assert follow_res.status_code == 200
    assert "Account created successfully! Please sign in." in follow_res.get_data(as_text=True)

    # Verify user record in database
    conn = get_db(db_file)
    try:
        user = get_user_by_email("aarav.sharma@example.com", db_file)
        assert user is not None
        assert user["name"] == "Aarav Sharma"
        assert user["email"] == "aarav.sharma@example.com"
        assert check_password_hash(user["password_hash"], "securepassword123")
        assert user["password_hash"] != "securepassword123"
    finally:
        conn.close()


def test_create_user_and_get_user_by_email_helpers(tmp_path):
    db_file = str(tmp_path / "helper_test.db")
    init_db(db_file)

    # get_user_by_email should return None for non-existent user
    assert get_user_by_email("none@example.com", db_file) is None

    # create_user helper test
    user_id = create_user("Kavita Nair", "kavita@example.com", "fake_hash_123", db_file)
    assert isinstance(user_id, int)
    assert user_id > 0

    # Retrieve user
    user = get_user_by_email("kavita@example.com", db_file)
    assert user is not None
    assert user["id"] == user_id
    assert user["name"] == "Kavita Nair"
    assert user["email"] == "kavita@example.com"

    # Case-insensitive retrieval
    user_upper = get_user_by_email("KAVITA@EXAMPLE.COM", db_file)
    assert user_upper is not None
    assert user_upper["id"] == user_id

    # Duplicate create_user should raise sqlite3.IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        create_user("Another Kavita", "kavita@example.com", "hash_456", db_file)
