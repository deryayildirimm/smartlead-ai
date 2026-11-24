from collections.abc import Mapping

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Genre, ReadingPreference, validate_timezone


class ReadingSettingsInputSerializer(serializers.Serializer):
    selection_mode = serializers.ChoiceField(choices=ReadingPreference.SelectionMode)
    target_minutes = serializers.IntegerField(min_value=1, max_value=60)
    genre_codes = serializers.ListField(
        child=serializers.SlugField(max_length=50), max_length=20, allow_empty=True
    )
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6), min_length=1, max_length=7
    )
    local_time = serializers.TimeField(input_formats=["%H:%M", "%H:%M:%S"])
    timezone = serializers.CharField(max_length=64)

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown_fields = set(data) - set(self.fields)
            if unknown_fields:
                raise serializers.ValidationError(
                    {field: "Bu alan kabul edilmiyor." for field in sorted(unknown_fields)}
                )
        return super().to_internal_value(data)

    def validate_genre_codes(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Aynı tür birden fazla kez seçilemez.")
        available = set(
            Genre.objects.filter(code__in=value, is_active=True).values_list("code", flat=True)
        )
        if set(value) != available:
            raise serializers.ValidationError("Yalnızca seçime açık türleri kullanın.")
        return sorted(value)

    def validate_weekdays(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Aynı gün birden fazla kez seçilemez.")
        return sorted(value)

    def validate_local_time(self, value):
        if value.second or value.microsecond:
            raise serializers.ValidationError("Saati dakika hassasiyetinde girin (ör. 09:30).")
        return value

    def validate_timezone(self, value):
        try:
            validate_timezone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value

    def validate(self, attrs):
        selected = attrs["selection_mode"] == ReadingPreference.SelectionMode.SELECTED
        if selected and not attrs["genre_codes"]:
            raise serializers.ValidationError({"genre_codes": "En az bir tür seçin."})
        if not selected and attrs["genre_codes"]:
            raise serializers.ValidationError(
                {"genre_codes": "Benim için seç modunda tür listesi boş olmalı."}
            )
        return attrs
