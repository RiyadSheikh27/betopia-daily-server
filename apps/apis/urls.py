from django.urls import path
from apps.products.views import (
    BrandListCreateView,
    BrandDetailView,
    BrandProductListView,
    CategoryListCreateView,
    CategoryDetailView,
    TagListCreateView,
    TagDetailView,
    ProductListCreateView,
    ProductDetailView,
    ProductImageUploadView,
    HotDealListView,
    ProductImageSetPrimaryView,
)
from apps.cart.views import (
    CartView,
    CartItemAddView,
    CartItemUpdateView,
    CartItemDeleteView,
    CartClearView,
)
from apps.site_settings.views import HeroImageView
from apps.user.views import UserProfileView

product_urlpatterns = [
    # Brand endpoints
    path("brands/", BrandListCreateView.as_view(), name="brand-list-create"),
    path("brands/<slug:slug>/", BrandDetailView.as_view(), name="brand-detail"),
    path(
        "brands/<slug:slug>/products/",
        BrandProductListView.as_view(),
        name="brand-product-list",
    ),
    # Category endpoints
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path(
        "categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"
    ),
    # Tag endpoints  (no slug — accessed by UUID)
    path("tags/", TagListCreateView.as_view(), name="tag-list-create"),
    path("tags/<uuid:pk>/", TagDetailView.as_view(), name="tag-detail"),
    # Product endpoints
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path(
        "products/<slug:slug>/images/",
        ProductImageUploadView.as_view(),
        name="product-images",
    ),
    # Hot deal endpoint
    path("hot-deals/", HotDealListView.as_view(), name="hot-deal-list"),
    # Is primary handler for product images
    path(
        "products/<slug:slug>/images/<uuid:image_id>/set-primary/",
        ProductImageSetPrimaryView.as_view(),
        name="product-image-set-primary",
    ),
    # User profile endpoint
    path("profile/", UserProfileView.as_view(), name="user-profile"),
]


site_settings_urlpatterns = [
    path("site-settings/hero/", HeroImageView.as_view(), name="hero-images"),
]

cart_urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemAddView.as_view(), name="cart-item-add"),
    path(
        "cart/items/<uuid:item_id>/",
        CartItemUpdateView.as_view(),
        name="cart-item-update",
    ),
    path(
        "cart/items/<uuid:item_id>/delete/",
        CartItemDeleteView.as_view(),
        name="cart-item-delete",
    ),
    path("cart/clear/", CartClearView.as_view(), name="cart-clear"),
]


urlpatterns = [
    *product_urlpatterns,
    *site_settings_urlpatterns,
    *cart_urlpatterns,
]
