from django.contrib import admin

from .models import ConsentEvent, DeliverySchedule, Genre, ReadingPreference


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "description")


@admin.register(ReadingPreference)
class ReadingPreferenceAdmin(ReadOnlyAdmin):
    list_display = ("user", "selection_mode", "target_minutes", "updated_at")
    search_fields = ("user__email",)


@admin.register(DeliverySchedule)
class DeliveryScheduleAdmin(ReadOnlyAdmin):
    list_display = ("user", "local_time", "timezone", "status", "version")
    list_filter = ("status",)
    search_fields = ("user__email",)


@admin.register(ConsentEvent)
class ConsentEventAdmin(ReadOnlyAdmin):
    list_display = ("user", "action", "text_version", "recorded_at")
    list_filter = ("action",)
    search_fields = ("user__email",)
