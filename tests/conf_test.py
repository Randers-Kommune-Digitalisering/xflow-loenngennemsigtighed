import os
from typing import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from main import create_app

os.environ.setdefault("FLASK_ENV", "dev")


@pytest.fixture()
def app() -> Iterator[Flask]:
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def test_healthz(client: FlaskClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
