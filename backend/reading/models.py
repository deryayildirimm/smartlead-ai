from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValidationError("Geçerli bir IANA saat dilimi seçin.") from exc


class Genre(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField("tür adı", max_length=80)
    description = models.TextField("açıklama", blank=True, default="")
    is_active = models.BooleanField("seçime açık", default=True)

    class Meta:
        ordering = ("code",)
        verbose_name = "tür"
        verbose_name_plural = "türler"

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField("yazar adı", max_length=200)

    class Meta:
        ordering = ("name", "pk")
        verbose_name = "yazar"
        verbose_name_plural = "yazarlar"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField("kitap adı", max_length=250)
    original_language = models.CharField(
        "özgün dil",
        max_length=10,
        blank=True,
        default="",
        help_text="Biliniyorsa dil kodu: tr, en, fr. Çeviri dili baskı kaydında tutulacak.",
    )
    description = models.TextField("açıklama", blank=True, default="")
    authors = models.ManyToManyField(
        Author, through="BookAuthor", related_name="books", verbose_name="yazarlar", blank=True
    )
    genres = models.ManyToManyField(
        Genre, through="BookGenre", related_name="books", verbose_name="türler", blank=True
    )
    created_at = models.DateTimeField("oluşturulma zamanı", auto_now_add=True)
    updated_at = models.DateTimeField("güncellenme zamanı", auto_now=True)

    class Meta:
        ordering = ("title", "pk")
        verbose_name = "kitap"
        verbose_name_plural = "kitaplar"

    def __str__(self):
        return self.title


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="author_links")
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name="book_links")
    position = models.PositiveSmallIntegerField(
        "yazar sırası", default=1, validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ("position", "pk")
        verbose_name = "kitap yazarı"
        verbose_name_plural = "kitap yazarları"
        constraints = [
            models.UniqueConstraint(fields=["book", "author"], name="reading_book_author_unique"),
            models.CheckConstraint(
                condition=models.Q(position__gte=1), name="reading_author_position_positive"
            ),
        ]


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="genre_links")
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, related_name="book_links")

    class Meta:
        verbose_name = "kitap türü"
        verbose_name_plural = "kitap türleri"
        constraints = [
            models.UniqueConstraint(fields=["book", "genre"], name="reading_book_genre_unique"),
        ]


class ReadingPreference(models.Model):
    class SelectionMode(models.TextChoices):
        SELECTED = "SELECTED", "Türlerimi seçtim"
        RANDOM = "RANDOM", "Benim için seç"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_preference"
    )
    selection_mode = models.CharField(max_length=8, choices=SelectionMode)
    target_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    language = models.CharField(max_length=5, default="tr", editable=False)
    genres = models.ManyToManyField(Genre, through="PreferenceGenre", related_name="preferences")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "okuma tercihi"
        verbose_name_plural = "okuma tercihleri"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_minutes__range=(1, 60)), name="reading_minutes_1_to_60"
            ),
            models.CheckConstraint(
                condition=models.Q(selection_mode__in=["SELECTED", "RANDOM"]),
                name="reading_valid_selection_mode",
            ),
            models.CheckConstraint(
                condition=models.Q(language="tr"), name="reading_initial_language_tr"
            ),
        ]

    def __str__(self):
        return str(self.user)


class PreferenceGenre(models.Model):
    preference = models.ForeignKey(ReadingPreference, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["preference", "genre"], name="reading_preference_genre_unique"
            )
        ]


class DeliverySchedule(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Taslak"
        ACTIVE = "ACTIVE", "Aktif"
        PAUSED = "PAUSED", "Duraklatıldı"
        STOPPED = "STOPPED", "Durduruldu"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_schedule"
    )
    local_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(
        max_length=64, default="Europe/Istanbul", validators=[validate_timezone]
    )
    status = models.CharField(max_length=8, choices=Status, default=Status.DRAFT)
    next_run_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "gönderim planı"
        verbose_name_plural = "gönderim planları"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="reading_schedule_version_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["DRAFT", "ACTIVE", "PAUSED", "STOPPED"]),
                name="reading_valid_schedule_status",
            ),
            models.CheckConstraint(
                condition=~models.Q(status="ACTIVE") | models.Q(local_time__isnull=False),
                name="reading_active_schedule_has_time",
            ),
        ]

    def __str__(self):
        return f"{self.user} / {self.get_status_display()}"


class ScheduleDay(models.Model):
    schedule = models.ForeignKey(DeliverySchedule, on_delete=models.CASCADE, related_name="days")
    weekday = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )

    class Meta:
        ordering = ("weekday",)
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "weekday"], name="reading_schedule_day_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(weekday__range=(0, 6)), name="reading_weekday_0_to_6"
            ),
        ]


class ConsentEvent(models.Model):
    class Action(models.TextChoices):
        GRANTED = "GRANTED", "Verildi"
        WITHDRAWN = "WITHDRAWN", "Geri çekildi"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="consent_events"
    )
    purpose = models.CharField(max_length=40, default="reading_delivery", editable=False)
    channel = models.CharField(max_length=10, default="EMAIL", editable=False)
    action = models.CharField(max_length=9, choices=Action)
    text_version = models.CharField(max_length=80)
    recorded_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=80)
    email_at_event = models.EmailField()

    class Meta:
        verbose_name = "gönderim izni olayı"
        verbose_name_plural = "gönderim izni geçmişi"
        ordering = ("-recorded_at", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(action__in=["GRANTED", "WITHDRAWN"]),
                name="reading_valid_consent_action",
            ),
        ]
