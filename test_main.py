# Copyright 2020 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
import pytest
import main


@pytest.fixture
def client(monkeypatch):
    main.app.testing = True

    class FakeRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value):
            self.data[key] = value
            return True

    monkeypatch.setattr(main, "redis_db", FakeRedis())
    return main.app.test_client()


def test_get_cart(client):
    response = client.get("/cart/123")

    assert response.status_code == 200
    assert response.get_json() == {
        "user_id": "123",
        "cart": None,
    }


def test_add_to_cart(client):
    response = client.post("/cart/123")

    assert response.status_code == 201
    assert response.get_json() == {
        "message": "Items added to cart for user 123"
    }


def test_cart_after_adding_items(client):
    client.post("/cart/123")
    response = client.get("/cart/123")

    assert response.status_code == 200
    assert response.get_json() == {
        "user_id": "123",
        "cart": "item1, item2, item3",
    }