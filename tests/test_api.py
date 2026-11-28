# --------------------------------------------------
# Shared test credentials
# --------------------------------------------------

TEST_USERNAME = "test_analyst"
TEST_PASSWORD = "SecurePassword2026!"
TEST_FULL_NAME = "Test Analyst"


# --------------------------------------------------
# Helper: Register and login
# --------------------------------------------------

def register_and_login(client):

    # Register a test user
    registration = client.post(
        "/auth/register",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "full_name": TEST_FULL_NAME,
        }
    )

    assert registration.status_code == 201, (
        f"Registration failed: {registration.json()}"
    )

    # Login using the same credentials
    login = client.post(
        "/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        }
    )

    assert login.status_code == 200, (
        f"Login failed: {login.json()}"
    )

    token = login.json()["access_token"]

    return token


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "Healthy"


# --------------------------------------------------
# Authentication
# --------------------------------------------------

def test_user_registration(client):

    response = client.post(
        "/auth/register",
        json={
            "username": "new_analyst",
            "password": "SecurePassword2026!",
            "full_name": "New Analyst",
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
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "full_name": TEST_FULL_NAME,
        }
    )

    assert response.status_code == 409


def test_invalid_login(client):

    # Create a valid user first
    register_and_login(client)

    # Attempt login with an incorrect password
    response = client.post(
        "/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": "WrongPassword2026!",
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
    assert response.json()["username"] == TEST_USERNAME


def test_analyst_cannot_access_admin_endpoint(client):

    token = register_and_login(client)

    response = client.get(
        "/auth/admin-check",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


# --------------------------------------------------
# Customer endpoints
# --------------------------------------------------

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


# --------------------------------------------------
# Product endpoints
# --------------------------------------------------

def test_get_product(client):

    token = register_and_login(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Get available products
    products_response = client.get(
        "/products",
        headers=headers,
    )

    assert products_response.status_code == 200

    products = products_response.json()

    assert len(products) == 1

    product_id = products[0]["product_id"]

    # Fetch that product
    response = client.get(
        f"/products/{product_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id
    assert data["product_name"] == products[0]["product_name"]


def test_list_products(client):

    token = register_and_login(client)

    response = client.get(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    products = response.json()

    assert len(products) == 1
    assert products[0]["product_id"] is not None
    assert products[0]["product_name"]

# --------------------------------------------------
# Metrics endpoint
# --------------------------------------------------

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


# --------------------------------------------------
# Sales analysis validation
# --------------------------------------------------

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
            "analysis_type": "revenue",
        }
    )

    assert response.status_code == 422