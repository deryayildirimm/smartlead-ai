from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections

from reading.models import DeliverySchedule, Genre, PreferenceGenre, ReadingPreference, ScheduleDay
from reading.serializers import ReadingSettingsInputSerializer
from reading.services import save_reading_settings


@pytest.mark.django_db(transaction=True)
def test_simultaneous_first_saves_create_one_complete_revision(reader, settings_payload):
    for code in settings_payload["genre_codes"]:
        Genre.objects.get_or_create(code=code, defaults={"name": code})
    serializer = ReadingSettingsInputSerializer(data=settings_payload)
    serializer.is_valid(raise_exception=True)
    barrier = Barrier(2)

    def save_from_separate_connection():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return save_reading_settings(reader, serializer.validated_data)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(save_from_separate_connection) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]

    assert results[0] == results[1]
    assert results[0]["version"] == 1
    assert ReadingPreference.objects.count() == 1
    assert DeliverySchedule.objects.count() == 1
    assert PreferenceGenre.objects.count() == 2
    assert ScheduleDay.objects.count() == 3
