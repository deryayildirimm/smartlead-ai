from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from accounts.views import MeView
from core.views import liveness, readiness
from reading.views import GenreListView, ReadingSettingsView

admin.site.site_header = "PassagePort Yönetim"
admin.site.site_title = "PassagePort"
admin.site.index_title = "Yönetim paneli"

urlpatterns = [
    path("health/", liveness, name="health"),
    path("health/ready/", readiness, name="readiness"),
    path("admin/", admin.site.urls),
    path("api/v1/genres/", GenreListView.as_view(), name="genres"),
    path("api/v1/me/", MeView.as_view(), name="me"),
    path("api/v1/me/reading-settings/", ReadingSettingsView.as_view(), name="reading-settings"),
]
if settings.DEBUG:
    urlpatterns += [path("api-auth/", include("rest_framework.urls"))]
