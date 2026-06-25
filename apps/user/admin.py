from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "uid",
        "employee_id",
        "email",
        "company",
        "company_address",
        'microsoft_access_token',
        "user_type",
        "role",
        "created_at",
    ]
    list_filter = ["role", "user_type"]
    search_fields = ["email", "company", "company_address", "employee_id", "uid"]
    readonly_fields = [
        "uid",
        "employee_id",
        "email",
        "user_type",
        "company",
        "company_address",
        "avatar",
        "phone",
        "access_token",
        "created_at",
        "updated_at",
    ]
    fields = [
        "uid",
        "employee_id",
        "email",
        "user_type",
        "company",
        "company_address",
        "avatar",
        "phone",
        "microsoft_access_token",
        "access_token",
        "role",
        "created_at",
        "updated_at",
    ]
