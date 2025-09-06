from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("message", "is_read", "timestamp", "user")
    list_filter = ("is_read", "timestamp")
    search_fields = ("message", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("timestamp",)
    fieldsets = (
        (None, {"fields": ("user", "message", "is_read")}),
        ("Date Information", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )
    ordering = ("-timestamp",)