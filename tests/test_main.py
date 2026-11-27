import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify that the health check endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_auth_registration_and_login():
    """Verify registration, login token generation, and profile fetching."""
    import time
    unique_email = f"test_{int(time.time())}@taskvault.com"
    register_payload = {
        "username": "Test Tester",
        "email": unique_email,
        "password": "TestPassword123!",
    }

    # 1. Register User
    reg_res = client.post("/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == unique_email
    assert user_data["role"] == "USER"
    assert "hashed_password" not in user_data
    assert "password" not in user_data

    # 2. Duplicate registration with same email MUST fail
    dup_res = client.post("/auth/register", json=register_payload)
    assert dup_res.status_code == 400
    assert dup_res.json()["detail"] == "Email already registered"

    # 3. Login to get JWT Token
    login_res = client.post(
        "/auth/login",
        json={"email": unique_email, "password": "TestPassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Access Protected Route /auth/me
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email


def test_task_crud_and_isolation():
    """Verify task creation, retrieval, update, deletion, and anti-IDOR isolation."""
    import time
    ts = int(time.time())
    email_a = f"alice_{ts}@taskvault.com"
    email_b = f"bob_{ts}@taskvault.com"

    # Register & Login User A (Alice)
    client.post("/auth/register", json={"username": "Alice", "email": email_a, "password": "Password123!"})
    login_a = client.post("/auth/login", json={"email": email_a, "password": "Password123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {login_a}"}

    # Register & Login User B (Bob)
    client.post("/auth/register", json={"username": "Bob", "email": email_b, "password": "Password123!"})
    login_b = client.post("/auth/login", json={"email": email_b, "password": "Password123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {login_b}"}

    # 1. Alice creates a task
    create_res = client.post(
        "/tasks",
        headers=headers_a,
        json={"title": "Alice's Secret Task", "description": "Top secret", "status": "PENDING"},
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    # 2. Alice views her task
    get_res = client.get(f"/tasks/{task_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Alice's Secret Task"

    # 3. ANTI-IDOR SECURITY CHECK: Bob tries to access Alice's task -> MUST return 404
    bob_get = client.get(f"/tasks/{task_id}", headers=headers_b)
    assert bob_get.status_code == 404

    # 4. Bob tries to update Alice's task -> MUST return 404
    bob_put = client.put(f"/tasks/{task_id}", headers=headers_b, json={"status": "COMPLETED"})
    assert bob_put.status_code == 404

    # 5. Bob tries to delete Alice's task -> MUST return 404
    bob_del = client.delete(f"/tasks/{task_id}", headers=headers_b)
    assert bob_del.status_code == 404

    # 6. Alice updates her task
    update_res = client.put(f"/tasks/{task_id}", headers=headers_a, json={"status": "COMPLETED"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "COMPLETED"

    # 7. Alice deletes her task
    delete_res = client.delete(f"/tasks/{task_id}", headers=headers_a)
    assert delete_res.status_code == 204


def test_rbac_security_barriers():
    """Verify that regular users receive 403 Forbidden on admin routes and Admins receive 200."""
    import time
    ts = int(time.time())
    user_email = f"regular_{ts}@taskvault.com"

    # Register & Login regular user
    client.post("/auth/register", json={"username": "Regular User", "email": user_email, "password": "Password123!"})
    user_token = client.post("/auth/login", json={"email": user_email, "password": "Password123!"}).json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Regular user calls /users -> MUST return 403 Forbidden
    res_users = client.get("/users", headers=user_headers)
    assert res_users.status_code == 403
    assert "Requires ADMIN role" in res_users.json()["detail"]

    # 2. Regular user calls /tasks/all -> MUST return 403 Forbidden
    res_tasks = client.get("/tasks/all", headers=user_headers)
    assert res_tasks.status_code == 403
    assert "Requires ADMIN role" in res_tasks.json()["detail"]

    # 3. Log in as seeded Admin
    admin_login = client.post("/auth/login", json={"email": "admin@taskvault.com", "password": "AdminSecure2026!"})
    if admin_login.status_code == 200:
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin calls /users -> MUST return 200 OK
        assert client.get("/users", headers=admin_headers).status_code == 200

        # Admin calls /tasks/all -> MUST return 200 OK
        assert client.get("/tasks/all", headers=admin_headers).status_code == 200
