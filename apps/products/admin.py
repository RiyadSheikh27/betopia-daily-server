from django.contrib import admin
from .models import Brand, Category, Tag, Product, ProductImage


# Brand admin
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug", "created_at", "updated_at"]


# Category admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug", "created_at", "updated_at"]


# Tag admin
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


# Product image inline for product admin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "is_primary"]


# Product admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "brand", "category", "price", "discount_amount", "discounted_price", "in_stock", "status", "is_hot_deal"]
    list_filter = ["brand", "category", "in_stock", "is_hot_deal", "status"]
    search_fields = ["name", "slug", "sku"]
    readonly_fields = ["slug", "discounted_price", "created_at", "updated_at"]
    inlines = [ProductImageInline]
    filter_horizontal = ["tags"]