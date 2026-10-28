from unittest.mock import patch

import pytest
from django.db import OperationalError


def test_liveness_is_public_without_database(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_hides_database_error_details(client):
    with patch(
        "core.views.connection.cursor", side_effect=OperationalError("private connection details")
    ):
        response = client.get("/health/ready/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


@pytest.mark.django_db
def test_readiness_checks_real_database(client):
    response = client.get("/health/ready/")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
