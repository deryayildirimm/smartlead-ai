import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required in production.")
if SECRET_KEY.startswith("passageport-test-only"):  # noqa: F405
    raise ImproperlyConfigured("A test secret must not be used in production.")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# Enable only behind a proxy that strips incoming X-Forwarded-Proto headers.
if os.environ.get("DJANGO_TRUST_PROXY", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
