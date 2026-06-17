from django.contrib import admin
from .models import HeroImage


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "created_at"]
    ordering = ["order"]