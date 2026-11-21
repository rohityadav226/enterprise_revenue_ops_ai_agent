
def register_and_login(client):

    # Register a test analyst

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Test Analyst"
            "username": "analyst_test",
            "password": "TestPassword2026!"
        }
    )

    assert registration.status_code == 201

    # Login and retrieve access token

    login = client.post(
        "/auth/login",
        json={
            "full_name": "Test Analyst"
            "username": "analyst_test",
            "password": "TestPassword2026!"
        }
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "Healthy"


def test_user_registration(client):

    response = client.post(
        "/auth/register",
        json={
            "username": "new_analyst",
            "password": "SecurePassword2026!"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "new_analyst"
    assert data["role"] == "revops_analyst"

    # Sensitive credentials must not be returned
    assert "password" not in data
    assert "hashed_password" not in data


def test_duplicate_username(client):

    register_and_login(client)

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Analyst"
            "username": "analyst_test",
            "password": "AnotherPassword2026!"
        }
    )

    assert response.status_code == 409


def test_invalid_login(client):

    register_and_login(client)

    response = client.post(
        "/auth/login",
        json={
            "full_name": "Test Analyst"
            "username": "analyst_test",
            "password": "WrongPassword2026!"
        }
    )

    assert response.status_code == 401


def test_current_user(client):

    token = register_and_login(client)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["username"] == "analyst_test"


def test_customer_requires_authentication(client):

    response = client.get("/customers/101")

    assert response.status_code == 401


def test_get_customer(client):

    token = register_and_login(client)

    response = client.get(
        "/customers/101",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Customer"


def test_customer_not_found(client):

    token = register_and_login(client)

    response = client.get(
        "/customers/999",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 404


def test_get_product(client):

    token = register_and_login(client)

    response = client.get(
        "/products/4000",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["product_name"] == "Test Laptop"


def test_get_metrics(client):

    token = register_and_login(client)

    response = client.get(
        "/metrics?period=monthly&region=north",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["revenue"] == 1250000


def test_invalid_sales_analysis(client):

    token = register_and_login(client)

    response = client.post(
        "/sales-analysis",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "start_date": "2026-10-31",
            "end_date": "2026-10-01",
            "minimum_revenue": 500000,
            "region": "north",
            "analysis_type": "revenue"
        }
    )

    assert response.status_code == 422


def test_analyst_cannot_access_admin_endpoint(client):

    token = register_and_login(client)

    response = client.get(
        "/auth/admin-check",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

def test_list_products(client):

    token = register_and_login(client)

    response = client.get(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["product_id"] == 4000
