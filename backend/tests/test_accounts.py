import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from accounts.models import ExternalIdentity, User

pytestmark = pytest.mark.django_db


def test_reader_email_is_normalized_without_a_local_password():
    user = User.objects.create_user("  Derya@Example.COM ")
    assert user.email == "derya@example.com"
    assert user.has_usable_password() is False
    assert user.is_staff is False
    assert user.email_verified_at is None


def test_email_uniqueness_is_case_insensitive_even_for_direct_updates(reader):
    other = User.objects.create_user("other@example.com")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=other.pk).update(email=reader.email.upper())


def test_superuser_flags_and_password():
    user = User.objects.create_superuser("admin@example.com", "an-example-test-password")
    assert user.is_staff and user.is_superuser
    assert user.check_password("an-example-test-password")
    with pytest.raises(ValueError):
        User.objects.create_superuser("bad@example.com", "password", is_staff=False)
    with pytest.raises(ValueError):
        User.objects.create_superuser("bad@example.com", None)


def test_external_identity_is_unique_per_provider_and_site(reader):
    other = User.objects.create_user("other@example.com")
    identity = {"provider": "wix", "site_id": "site-1", "subject": "member-1"}
    ExternalIdentity.objects.create(user=reader, **identity)
    with pytest.raises(IntegrityError), transaction.atomic():
        ExternalIdentity.objects.create(user=other, **identity)
    ExternalIdentity.objects.create(user=other, **{**identity, "site_id": "site-2"})


def test_me_exposes_only_current_user(api, reader):
    other = User.objects.create_user("other@example.com")
    response = api.get("/api/v1/me/", {"user_id": str(other.pk)})
    assert response.status_code == 200
    assert response.data == {
        "id": str(reader.pk),
        "email": reader.email,
        "display_name": "Okuyucu",
        "email_verified": False,
    }


def test_inactive_session_cannot_read_profile(reader):
    reader.set_password("an-example-test-password")
    reader.save()
    client = APIClient()
    client.force_login(reader)
    reader.is_active = False
    reader.save()
    assert client.get("/api/v1/me/").status_code == 403


def test_admin_login_is_separate_from_reader_access(reader):
    client = APIClient()
    client.force_login(reader)
    assert client.get("/admin/").status_code == 302
    admin = User.objects.create_superuser("admin@example.com", "an-example-test-password")
    client.force_login(admin)
    assert client.get("/admin/").status_code == 200
    assert client.get("/admin/accounts/user/add/").status_code == 200
    assert client.get(f"/admin/accounts/user/{reader.pk}/change/").status_code == 200


def test_staff_login_accepts_normalized_email():
    User.objects.create_superuser("admin@example.com", "an-example-test-password")
    client = APIClient()
    assert client.login(email="ADMIN@EXAMPLE.COM", password="an-example-test-password")
