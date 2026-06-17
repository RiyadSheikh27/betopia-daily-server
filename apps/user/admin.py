from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["uid", "employee_id", "email", "company", "user_type", "role", "created_at"]
    list_filter = ["role", "user_type"]
    search_fields = ["email", "company", "employee_id", "uid"]
    readonly_fields = ["uid", "employee_id", "email", "user_type", "company", "created_at", "updated_at"]
    fields = ["uid", "employee_id", "email", "user_type", "company", "role", "created_at", "updated_at"]