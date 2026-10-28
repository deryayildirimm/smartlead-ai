import pytest
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture
def reader(db):
    return User.objects.create_user("reader@example.com", display_name="Okuyucu")


@pytest.fixture
def api(reader):
    client = APIClient()
    client.force_authenticate(user=reader)
    return client


@pytest.fixture
def settings_payload():
    return {
        "selection_mode": "SELECTED",
        "target_minutes": 5,
        "genre_codes": ["fantasy", "philosophy"],
        "weekdays": [0, 2, 4],
        "local_time": "09:30",
        "timezone": "Europe/Istanbul",
    }
