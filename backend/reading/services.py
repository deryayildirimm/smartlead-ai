from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User

from .models import DeliverySchedule, Genre, PreferenceGenre, ReadingPreference, ScheduleDay


def _lock_user(user):
    locked = User.objects.select_for_update().get(pk=user.pk)
    if not locked.is_active:
        raise PermissionDenied("Hesap erişime kapalı.")
    return locked


def _snapshot(user):
    preference = ReadingPreference.objects.filter(user=user).first()
    schedule = DeliverySchedule.objects.filter(user=user).first()
    return {
        "configured": preference is not None and schedule is not None,
        "selection_mode": preference.selection_mode if preference else None,
        "target_minutes": preference.target_minutes if preference else None,
        "language": preference.language if preference else "tr",
        "genre_codes": list(preference.genres.values_list("code", flat=True)) if preference else [],
        "weekdays": list(schedule.days.values_list("weekday", flat=True)) if schedule else [],
        "local_time": schedule.local_time.strftime("%H:%M")
        if schedule and schedule.local_time
        else None,
        "timezone": schedule.timezone if schedule else "Europe/Istanbul",
        "schedule_status": schedule.status if schedule else DeliverySchedule.Status.DRAFT,
        "version": schedule.version if schedule else None,
    }


@transaction.atomic
def get_reading_settings(user):
    # Readers and writers take the same lock so a response cannot mix two revisions.
    return _snapshot(_lock_user(user))


@transaction.atomic
def save_reading_settings(user, data):
    user = _lock_user(user)
    # Recheck availability inside the transaction; genres may have changed after validation.
    genres = list(
        Genre.objects.select_for_update()
        .filter(code__in=data["genre_codes"], is_active=True)
        .order_by("code")
    )
    if {genre.code for genre in genres} != set(data["genre_codes"]):
        raise ValidationError({"genre_codes": "Tür listesi değişti. Yeniden seçim yapın."})

    previous = _snapshot(user)
    incoming = {
        key: data[key]
        for key in ("selection_mode", "target_minutes", "genre_codes", "weekdays", "timezone")
    }
    incoming["local_time"] = data["local_time"].strftime("%H:%M")
    if previous["configured"] and all(previous[key] == value for key, value in incoming.items()):
        return previous

    preference, _ = ReadingPreference.objects.update_or_create(
        user=user,
        defaults={
            "selection_mode": data["selection_mode"],
            "target_minutes": data["target_minutes"],
        },
    )
    PreferenceGenre.objects.filter(preference=preference).delete()
    PreferenceGenre.objects.bulk_create(
        [PreferenceGenre(preference=preference, genre=genre) for genre in genres]
    )
    schedule, created = DeliverySchedule.objects.get_or_create(user=user)
    schedule.local_time = data["local_time"]
    schedule.timezone = data["timezone"]
    schedule.next_run_at = None
    if not created:
        schedule.version += 1
    # Saving preferences never grants consent or activates delivery.
    schedule.save()
    schedule.days.all().delete()
    ScheduleDay.objects.bulk_create(
        [ScheduleDay(schedule=schedule, weekday=weekday) for weekday in data["weekdays"]]
    )
    return _snapshot(user)
