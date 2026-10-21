import pytest
import main


VALID_ITEM = {
    "product_id": "ABC123",
    "name": "Keyboard",
    "description": "Wireless keyboard",
    "price_usd": 29.99,
    "categories": ["electronics", "office"],
}


@pytest.fixture
def client(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value):
            self.data[key] = value
            return True

        def delete(self, key):
            return self.data.pop(key, None) is not None

    monkeypatch.setattr(main, "redis_db", FakeRedis())
    main.app.testing = True
    return main.app.test_client()


def test_get_empty_cart(client):
    response = client.get("/cart/123")

    assert response.status_code == 200
    assert response.get_json() == {
        "user_id": "123",
        "cart": None,
    }


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("GET", {}),
        ("POST", {"json": VALID_ITEM}),
        ("DELETE", {}),
    ],
)
def test_routes_log_correlation_id(client, monkeypatch, method, kwargs):
    logged_messages = []
    monkeypatch.setattr(main.logger, "log_text", logged_messages.append)

    response = client.open(
        "/cart/123",
        method=method,
        headers={"correlation_id": "corr-123"},
        **kwargs,
    )

    assert response.status_code in {200, 201}
    assert len(logged_messages) == 1
    assert "Correlation ID: corr-123" in logged_messages[0]


def test_redis_failure_returns_service_unavailable(client, monkeypatch):
    def raise_connection_error(key):
        raise main.redis.exceptions.ConnectionError("Redis is unavailable")

    monkeypatch.setattr(main.redis_db, "get", raise_connection_error)

    response = client.get("/cart/123")

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "Cart service is temporarily unavailable"
    }


def test_add_valid_item(client):
    response = client.post("/cart/123", json=VALID_ITEM)

    assert response.status_code == 201
    assert response.get_json()["item"] == VALID_ITEM


def test_add_item_with_price_alias(client):
    item_with_price = {**VALID_ITEM, "price": VALID_ITEM["price_usd"]}
    del item_with_price["price_usd"]

    response = client.post("/cart/123", json=item_with_price)

    assert response.status_code == 201
    assert response.get_json()["item"] == VALID_ITEM


def test_get_cart_after_adding_item(client):
    client.post("/cart/123", json=VALID_ITEM)

    response = client.get("/cart/123")

    assert response.status_code == 200
    assert response.get_json()["cart"] == [VALID_ITEM]


@pytest.mark.parametrize("invalid_item", [
    {},
    {"product_id": "ABC123"},
    {**VALID_ITEM, "extra": "field"},
    {**VALID_ITEM, "product_id": ""},
    {**VALID_ITEM, "price_usd": -1},
    {**VALID_ITEM, "price_usd": "29.99"},
    {**VALID_ITEM, "price": VALID_ITEM["price_usd"]},
    {**VALID_ITEM, "categories": []},
    {**VALID_ITEM, "categories": ["electronics", 123]},
])
def test_rejects_invalid_items(client, invalid_item):
    response = client.post("/cart/123", json=invalid_item)

    assert response.status_code == 400


def test_delete_cart(client):
    client.post("/cart/123", json=VALID_ITEM)

    response = client.delete("/cart/123")

    assert response.status_code == 200

    response = client.get("/cart/123")
    assert response.get_json()["cart"] is None