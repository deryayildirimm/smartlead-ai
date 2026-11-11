import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email or not email.strip():
            raise ValueError("E-posta adresi gereklidir.")
        user = self.model(email=email.strip().lower(), **extra_fields)
        user.set_password(password)  # None creates an unusable password for Wix readers.
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Yönetici için is_staff=True gereklidir.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Yönetici için is_superuser=True gereklidir.")
        if not password:
            raise ValueError("Yönetici parolası gereklidir.")
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email.strip())


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("e-posta adresi", unique=True)
    display_name = models.CharField("görünen ad", max_length=150, blank=True)
    email_verified_at = models.DateTimeField("e-posta doğrulama zamanı", null=True, blank=True)
    is_active = models.BooleanField("hesap açık", default=True)
    is_staff = models.BooleanField("yönetim paneline erişim", default=False)
    date_joined = models.DateTimeField("kayıt zamanı", default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "kullanıcı"
        verbose_name_plural = "kullanıcılar"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique")
        ]

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class ExternalIdentity(models.Model):
    class Provider(models.TextChoices):
        WIX = "wix", "Wix Members"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="external_identities")
    provider = models.CharField(max_length=20, choices=Provider, default=Provider.WIX)
    site_id = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "dış kimlik"
        verbose_name_plural = "dış kimlikler"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "site_id", "subject"], name="accounts_external_identity_unique"
            )
        ]

    def __str__(self):
        return f"{self.provider} / {self.user}"
