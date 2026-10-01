# Copyright 2020 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
import os
import pytest
import main


@pytest.fixture
def client():
    main.app.testing = True
    return main.app.test_client()


def test_handler_no_env_variable(client):
    r = client.get("/")
    assert r.data.decode() == "Hello World!"
    assert r.status_code == 200


def test_handler_with_env_variable(client):
    os.environ["NAME"] = "Foo"
    r = client.get("/")
    assert r.data.decode() == "Hello Foo!"
    assert r.status_code == 200