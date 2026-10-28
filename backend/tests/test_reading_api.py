from unittest.mock import patch

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from accounts.models import User
from reading.models import (
    ConsentEvent,
    DeliverySchedule,
    Genre,
    PreferenceGenre,
    ReadingPreference,
    ScheduleDay,
)
from reading.serializers import ReadingSettingsInputSerializer
from reading.services import save_reading_settings

pytestmark = pytest.mark.django_db
URL = "/api/v1/me/reading-settings/"


def test_anonymous_requests_cannot_read_or_save(settings_payload):
    client = APIClient()
    assert client.get("/api/v1/me/").status_code == 403
    assert client.get(URL).status_code == 403
    assert client.put(URL, settings_payload, format="json").status_code == 403
    assert not ReadingPreference.objects.exists()


def test_public_genres_include_fantasy_and_hide_inactive():
    Genre.objects.create(code="inactive", name="Kapalı tür", is_active=False)
    response = APIClient().get("/api/v1/genres/")
    assert response.status_code == 200
    assert {row["code"] for row in response.data} == {
        "science_fiction",
        "philosophy",
        "fantasy",
        "humor",
        "crime",
    }


def test_reading_defaults_do_not_create_records(api):
    response = api.get(URL)
    assert response.status_code == 200
    assert response.data["configured"] is False
    assert response.data["timezone"] == "Europe/Istanbul"
    assert response.data["schedule_status"] == "DRAFT"
    assert not ReadingPreference.objects.exists()
    assert not DeliverySchedule.objects.exists()


def test_save_and_reload_multiple_genres_and_days(api, reader, settings_payload):
    response = api.put(URL, settings_payload, format="json")
    assert response.status_code == 200, response.data
    for key, value in settings_payload.items():
        assert response.data[key] == value
    assert response.data["configured"] is True
    assert response.data["version"] == 1
    assert response.data["schedule_status"] == "DRAFT"
    assert api.get(URL).data == response.data
    assert ReadingPreference.objects.get().user_id == reader.pk
    assert PreferenceGenre.objects.count() == 2
    assert ScheduleDay.objects.count() == 3
    assert not ConsentEvent.objects.exists()
    assert DeliverySchedule.objects.get().next_run_at is None


def test_repeated_save_is_idempotent_even_if_lists_are_reordered(api, settings_payload):
    first = api.put(URL, settings_payload, format="json").data
    timestamp = ReadingPreference.objects.get().updated_at
    reordered = {
        **settings_payload,
        "genre_codes": ["philosophy", "fantasy"],
        "weekdays": [4, 0, 2],
    }
    second = api.put(URL, reordered, format="json")
    assert second.status_code == 200
    assert second.data == first
    assert ReadingPreference.objects.get().updated_at == timestamp
    assert ReadingPreference.objects.count() == 1
    assert DeliverySchedule.objects.count() == 1
    assert PreferenceGenre.objects.count() == 2
    assert ScheduleDay.objects.count() == 3


def test_changes_invalidate_schedule_and_increment_revision(api, settings_payload):
    api.put(URL, settings_payload, format="json")
    response = api.put(URL, {**settings_payload, "target_minutes": 10}, format="json")
    assert response.status_code == 200
    assert response.data["version"] == 2
    assert response.data["target_minutes"] == 10
    assert response.data["schedule_status"] == "DRAFT"


def test_random_mode_removes_previous_genre_selection(api, settings_payload):
    api.put(URL, settings_payload, format="json")
    response = api.put(
        URL, {**settings_payload, "selection_mode": "RANDOM", "genre_codes": []}, format="json"
    )
    assert response.status_code == 200
    assert response.data["selection_mode"] == "RANDOM"
    assert not PreferenceGenre.objects.exists()


def test_one_reader_cannot_read_or_overwrite_another(api, reader, settings_payload):
    api.put(URL, settings_payload, format="json")
    other = User.objects.create_user("other@example.com")
    other_api = APIClient()
    other_api.force_authenticate(user=other)
    assert other_api.get(URL, {"user_id": str(reader.pk)}).data["configured"] is False
    other_api.put(URL, {**settings_payload, "target_minutes": 15}, format="json")
    assert api.get(URL).data["target_minutes"] == 5
    assert other_api.get(URL).data["target_minutes"] == 15


@pytest.mark.parametrize(
    "field,value",
    [
        ("user_id", "another-reader"),
        ("is_staff", True),
        ("role", "admin"),
        ("schedule_status", "ACTIVE"),
        ("email_verified", True),
        ("language", "en"),
        ("version", 999),
    ],
)
def test_ownership_and_privilege_fields_are_rejected(api, settings_payload, field, value):
    response = api.put(URL, {**settings_payload, field: value}, format="json")
    assert response.status_code == 400
    assert field in response.data
    assert not ReadingPreference.objects.exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"target_minutes": 0},
        {"target_minutes": 61},
        {"target_minutes": 1.5},
        {"weekdays": []},
        {"weekdays": [7]},
        {"weekdays": [-1]},
        {"weekdays": [0, 0]},
        {"local_time": "25:00"},
        {"local_time": "09:30:01"},
        {"timezone": "Istanbul"},
        {"timezone": "../../etc/passwd"},
        {"genre_codes": []},
        {"genre_codes": ["fantasy", "fantasy"]},
        {"genre_codes": ["missing"]},
        {"selection_mode": "RANDOM"},
    ],
)
def test_invalid_settings_do_not_write_partial_data(api, settings_payload, changes):
    response = api.put(URL, {**settings_payload, **changes}, format="json")
    assert response.status_code == 400, response.data
    assert not ReadingPreference.objects.exists()
    assert not DeliverySchedule.objects.exists()


def test_inactive_genre_cannot_be_selected(api, settings_payload):
    Genre.objects.filter(code="fantasy").update(is_active=False)
    response = api.put(URL, settings_payload, format="json")
    assert response.status_code == 400


def test_genres_are_rechecked_after_validation(reader, settings_payload):
    serializer = ReadingSettingsInputSerializer(data=settings_payload)
    serializer.is_valid(raise_exception=True)
    Genre.objects.filter(code="fantasy").update(is_active=False)
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError):
        save_reading_settings(reader, serializer.validated_data)
    assert not ReadingPreference.objects.exists()


def test_update_rolls_back_all_tables_if_saving_schedule_days_fails(api, settings_payload):
    first = api.put(URL, settings_payload, format="json").data
    with patch(
        "reading.services.ScheduleDay.objects.bulk_create", side_effect=RuntimeError("failure")
    ):
        with pytest.raises(RuntimeError):
            api.put(URL, {**settings_payload, "target_minutes": 10}, format="json")
    assert api.get(URL).data == first


def test_database_enforces_weekday_and_duplicate_constraints(api, settings_payload):
    api.put(URL, settings_payload, format="json")
    schedule = DeliverySchedule.objects.get()
    with pytest.raises(IntegrityError), transaction.atomic():
        ScheduleDay.objects.create(schedule=schedule, weekday=7)
    with pytest.raises(IntegrityError), transaction.atomic():
        ScheduleDay.objects.create(schedule=schedule, weekday=0)
    preference = ReadingPreference.objects.get()
    with pytest.raises(IntegrityError), transaction.atomic():
        PreferenceGenre.objects.create(
            preference=preference, genre=Genre.objects.get(code="fantasy")
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        ReadingPreference.objects.filter(pk=preference.pk).update(target_minutes=0)


def test_session_write_requires_csrf(reader, settings_payload):
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(reader)
    assert client.get(URL).status_code == 200
    assert client.put(URL, settings_payload, format="json").status_code == 403
