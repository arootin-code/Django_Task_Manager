from django.contrib import admin

from jobs.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "status", "created_at", "finished_at")
    list_filter = ("status",)
    search_fields = ("title", "description", "user__username")
    readonly_fields = ("created_at", "finished_at")
    ordering = ("-created_at",)