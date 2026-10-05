import pytest
import main


VALID_ITEM = {
    "product_id": "ABC123",
    "name": "Keyboard",
    "description": "Wireless keyboard",
    "price": 29.99,
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


def test_add_valid_item(client):
    response = client.post("/cart/123", json=VALID_ITEM)

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
    {**VALID_ITEM, "price": -1},
    {**VALID_ITEM, "price": "29.99"},
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