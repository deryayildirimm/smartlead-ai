import re

from constants import ErrorMessages, ValidationRules
from app.exceptions import ValidationError


def require_object(data):
    if not isinstance(data, dict):
        raise ValidationError(
            ErrorMessages.INVALID_JSON_OBJECT
        )


def validate_chat(data):
    require_object(data)

    message = data.get("mesaj")
    history = data.get("gecmis", [])

    if not isinstance(message, str) or not message.strip():
        raise ValidationError(ErrorMessages.EMPTY_MESSAGE)

    if len(message) > ValidationRules.MAX_MESSAGE_LENGTH:
        raise ValidationError(
            ErrorMessages.MESSAGE_TOO_LONG.format(
                limit=ValidationRules.MAX_MESSAGE_LENGTH
            )
        )

    if not isinstance(history, list):
        raise ValidationError(
            ErrorMessages.HISTORY_MUST_BE_LIST
        )

    if len(history) > ValidationRules.MAX_HISTORY_COUNT:
        raise ValidationError(
            ErrorMessages.HISTORY_TOO_LONG.format(
                limit=ValidationRules.MAX_HISTORY_COUNT
            )
        )

    clean_history = []

    for item in history:
        if not isinstance(item, dict):
            raise ValidationError(
                ErrorMessages.INVALID_HISTORY_ITEM
            )

        role = item.get("role")
        content = item.get("content")

        if role not in ("user", "assistant"):
            raise ValidationError(
                ErrorMessages.INVALID_HISTORY_ROLE
            )

        if (
            not isinstance(content, str)
            or not content.strip()
            or len(content) > ValidationRules.MAX_HISTORY_MESSAGE_LENGTH
        ):
            raise ValidationError(
                ErrorMessages.INVALID_HISTORY_CONTENT
            )

        clean_history.append({
            "role": role,
            "content": content,
        })

    return message.strip(), clean_history


def validate_lead(data):
    require_object(data)

    cleaned = {}

    for field, limit in ValidationRules.FIELD_LIMITS.items():
        default = (
            ValidationRules.DEFAULT_SERIES
            if field == "seri"
            else ""
        )

        value = data.get(field, default)

        if not isinstance(value, str):
            raise ValidationError(
                ErrorMessages.FIELD_MUST_BE_TEXT.format(
                    field=field
                )
            )

        value = value.strip()

        if len(value) > limit:
            raise ValidationError(
                ErrorMessages.FIELD_TOO_LONG.format(
                    field=field,
                    limit=limit,
                )
            )

        cleaned[field] = value

    for field in ("isim", "telefon", "email"):
        if not cleaned[field]:
            raise ValidationError(
                ErrorMessages.FIELD_REQUIRED.format(
                    field=field
                )
            )

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        cleaned["email"],
    ):
        raise ValidationError(ErrorMessages.INVALID_EMAIL)

    if not re.fullmatch(
        r"\+?[0-9 ()-]{7,30}",
        cleaned["telefon"],
    ):
        raise ValidationError(ErrorMessages.INVALID_PHONE)

    digit_count = sum(
        character.isdigit()
        for character in cleaned["telefon"]
    )

    if not 7 <= digit_count <= 15:
        raise ValidationError(
            ErrorMessages.INVALID_PHONE_LENGTH
        )

    if cleaned["seri"] not in ValidationRules.ALLOWED_SERIES:
        raise ValidationError(ErrorMessages.INVALID_SERIES)

    return cleaned