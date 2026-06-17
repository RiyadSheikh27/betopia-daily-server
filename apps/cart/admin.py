from django.contrib import admin
from .models import Cart, CartItem


# Cart item inline
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ["product", "quantity"]
    readonly_fields = ["product"]


# Cart admin
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at"]
    search_fields = ["user__email"]
    inlines = [CartItemInline]
