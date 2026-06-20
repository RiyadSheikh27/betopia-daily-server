from django.contrib import admin
from .models import Order, OrderItem


# Order item inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["product_name", "unit", "price", "discounted_price", "quantity"]
    readonly_fields = ["product_name", "unit", "price", "discounted_price", "quantity"]


# Order admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "user", "status", "company", "total_amount", "created_at"]
    list_filter = ["status", "company"]
    search_fields = ["order_id", "user__email"]
    readonly_fields = ["order_id", "total_amount", "created_at", "updated_at"]
    inlines = [OrderItemInline]