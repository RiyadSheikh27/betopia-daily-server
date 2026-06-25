from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.utils.pagination import StandardPagination

from apps.utils.custom_response import APIResponse
from apps.user.permissions import (
    IsAdminOrReadOnly,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from .models import Brand, Category, Tag, Product, ProductImage
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    TagSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    ProductImageSerializer,
)

""" Helper functions and views for Brand, Category, Tag, Product, and ProductImage APIs. """


def handle_product_images(product, request):
    """Save uploaded images for a product. First image becomes primary if none exists."""
    images = request.FILES.getlist("images")
    if not images:
        return
    has_primary = product.images.filter(is_primary=True).exists()
    for index, image_file in enumerate(images):
        is_primary = index == 0 and not has_primary
        ProductImage.objects.create(
            product=product, image=image_file, is_primary=is_primary
        )


""" Views for Brand, Category, Tag, Product, and ProductImage APIs. """


# Brand views
class BrandListCreateView(APIView):
    """List all brands or create a new brand."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        brands = Brand.objects.annotate(product_count=Count("products"))
        serializer = BrandSerializer(brands, many=True, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data, message="Brand created successfully"
            )
        return APIResponse.error(errors=serializer.errors)


class BrandDetailView(APIView):
    """Retrieve, update or delete a brand."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, slug):
        try:
            return Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            return None

    def get(self, request, slug):
        brand = self.get_object(slug)
        if not brand:
            return APIResponse.error(message="Brand not found", status_code=404)
        serializer = BrandSerializer(brand, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def put(self, request, slug):
        brand = self.get_object(slug)
        if not brand:
            return APIResponse.error(message="Brand not found", status_code=404)
        serializer = BrandSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data, message="Brand updated successfully"
            )
        return APIResponse.error(errors=serializer.errors)

    def delete(self, request, slug):
        brand = self.get_object(slug)
        if not brand:
            return APIResponse.error(message="Brand not found", status_code=404)
        brand.delete()
        return APIResponse.success(message="Brand deleted successfully")


# Category views
class CategoryListCreateView(APIView):
    """List all categories or create a new category."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        categories = Category.objects.annotate(product_count=Count("products"))
        serializer = CategorySerializer(
            categories, many=True, context={"request": request}
        )
        return APIResponse.success(data=serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data, message="Category created successfully"
            )
        return APIResponse.error(errors=serializer.errors)


class CategoryDetailView(APIView):
    """Retrieve, update or delete a category."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, slug):
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return None

    def get(self, request, slug):
        category = self.get_object(slug)
        if not category:
            return APIResponse.error(message="Category not found", status_code=404)
        serializer = CategorySerializer(category, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def put(self, request, slug):
        category = self.get_object(slug)
        if not category:
            return APIResponse.error(message="Category not found", status_code=404)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data, message="Category updated successfully"
            )
        return APIResponse.error(errors=serializer.errors)

    def delete(self, request, slug):
        category = self.get_object(slug)
        if not category:
            return APIResponse.error(message="Category not found", status_code=404)
        category.delete()
        return APIResponse.success(message="Category deleted successfully")


# Tag views
class TagListCreateView(APIView):
    """List all tags or create a new tag."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return APIResponse.success(data=serializer.data)

    def post(self, request):
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data, message="Tag created successfully"
            )
        return APIResponse.error(errors=serializer.errors)


class TagDetailView(APIView):
    """Retrieve, update or delete a tag."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            return None

    def get(self, request, pk):
        tag = self.get_object(pk)
        if not tag:
            return APIResponse.error(message="Tag not found", status_code=404)
        return APIResponse.success(data=TagSerializer(tag).data)

    def put(self, request, pk):
        tag = self.get_object(pk)
        if not tag:
            return APIResponse.error(message="Tag not found", status_code=404)
        serializer = TagSerializer(tag, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data, message="Tag updated successfully"
            )
        return APIResponse.error(errors=serializer.errors)

    def delete(self, request, pk):
        tag = self.get_object(pk)
        if not tag:
            return APIResponse.error(message="Tag not found", status_code=404)
        tag.delete()
        return APIResponse.success(message="Tag deleted successfully")


# Product helper
def annotate_product_sales(queryset):
    return queryset.annotate(
        sold_count=Coalesce(
            Sum(
                "order_items__quantity",
                filter=Q(order_items__order__status__in=["accepted", "delivered"]),
            ),
            0,
        )
    )


def apply_product_filters(queryset, request):
    brand_slug = request.query_params.get("brand")
    category_slug = request.query_params.get("category")
    search = request.query_params.get("search")
    sort = request.query_params.get("sort")
    in_stock = request.query_params.get("in_stock")
    status = request.query_params.get("status")

    if brand_slug:
        queryset = queryset.filter(brand__slug=brand_slug)
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    if in_stock is not None:
        queryset = queryset.filter(in_stock=in_stock.lower() == "true")

    # Show only active by default, status=false shows inactive
    if status is not None:
        queryset = queryset.filter(status=status.lower() == "true")
    else:
        queryset = queryset.filter(status=True)

    if sort == "price_low":
        queryset = queryset.order_by("discounted_price")
    elif sort == "price_high":
        queryset = queryset.order_by("-discounted_price")
    elif sort == "best_sell":
        queryset = queryset.order_by("-sold_count")
    elif sort == "top_review":
        queryset = queryset.order_by("-avg_rating")

    return queryset


# Product list and create
class ProductListCreateView(APIView):
    """
    List all products with filters.
    Supports brand, category, search, sort, in_stock query params.
    brand and category filters now accept slug values.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        products = Product.objects.select_related("brand", "category").prefetch_related(
            "images", "tags"
        )
        products = annotate_product_sales(products)
        products = apply_product_filters(products, request)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(
            page, many=True, context={"request": request}
        )
        return APIResponse.paginated(
            data=serializer.data,
            pagination_meta=paginator.get_paginated_meta(),
        )

    def post(self, request):
        serializer = ProductWriteSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            handle_product_images(product, request)
            return APIResponse.success(
                data=ProductDetailSerializer(
                    product, context={"request": request}
                ).data,
                message="Product created successfully",
            )
        return APIResponse.error(errors=serializer.errors)


# Product detail, update, delete
class ProductDetailView(APIView):
    """Retrieve, update or delete a product."""

    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, slug):
        try:
            return annotate_product_sales(
                Product.objects.select_related("brand", "category").prefetch_related(
                    "images", "tags"
                )
            ).get(slug=slug)
        except Product.DoesNotExist:
            return None

    def get(self, request, slug):
        product = self.get_object(slug)
        if not product:
            return APIResponse.error(message="Product not found", status_code=404)
        serializer = ProductDetailSerializer(product, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def put(self, request, slug):
        product = self.get_object(slug)
        if not product:
            return APIResponse.error(message="Product not found", status_code=404)
        serializer = ProductWriteSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            handle_product_images(updated, request)
            return APIResponse.success(
                data=ProductDetailSerializer(
                    updated, context={"request": request}
                ).data,
                message="Product updated successfully",
            )
        return APIResponse.error(errors=serializer.errors)

    def delete(self, request, slug):
        product = self.get_object(slug)
        if not product:
            return APIResponse.error(message="Product not found", status_code=404)
        product.delete()
        return APIResponse.success(message="Product deleted successfully")


# Product images
class ProductImageUploadView(APIView):
    """Upload one or more images to a product."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return APIResponse.error(message="Product not found", status_code=404)

        images = request.FILES.getlist("images")
        if not images:
            return APIResponse.error(message="No images provided")

        has_primary = product.images.filter(is_primary=True).exists()

        # If client is uploading a new primary, clear the existing one first
        is_setting_new_primary = (
            request.data.get("is_primary", "false").lower() == "true"
        )
        if is_setting_new_primary and has_primary:
            ProductImage.objects.filter(product=product, is_primary=True).update(
                is_primary=False
            )
            has_primary = False

        created = []
        for index, image_file in enumerate(images):
            is_primary = index == 0 and not has_primary
            img = ProductImage.objects.create(
                product=product, image=image_file, is_primary=is_primary
            )
            created.append(img)

        serializer = ProductImageSerializer(
            created, many=True, context={"request": request}
        )
        return APIResponse.success(
            data=serializer.data, message="Images uploaded successfully"
        )

    def delete(self, request, slug):
        """Delete a specific image by image_id in request body."""
        image_id = request.data.get("image_id")
        if not image_id:
            return APIResponse.error(message="image_id is required")
        try:
            image = ProductImage.objects.get(pk=image_id, product__slug=slug)
            image.delete()
            return APIResponse.success(message="Image deleted successfully")
        except ProductImage.DoesNotExist:
            return APIResponse.error(message="Image not found", status_code=404)


# Hot deal list
class HotDealListView(APIView):
    """
    List all active hot deal products.
    Active means is_hot_deal=True and within validity period.
    Supports same filters as product list.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        now = timezone.now()
        products = (
            Product.objects.select_related("brand", "category")
            .prefetch_related("images", "tags")
            .filter(is_hot_deal=True)
            .filter(Q(hot_deal_start__isnull=True) | Q(hot_deal_start__lte=now))
            .filter(Q(hot_deal_end__isnull=True) | Q(hot_deal_end__gte=now))
        )
        products = apply_product_filters(products, request)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(
            page, many=True, context={"request": request}
        )
        return APIResponse.paginated(
            data=serializer.data,
            pagination_meta=paginator.get_paginated_meta(),
        )


# Brand product list
class BrandProductListView(APIView):
    """
    List all products under a specific brand.
    Supports same filters as product list except brand filter.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, slug):
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            return APIResponse.error(message="Brand not found", status_code=404)

        products = (
            Product.objects.select_related("brand", "category")
            .prefetch_related("images", "tags")
            .filter(brand=brand)
        )
        products = apply_product_filters(products, request)
        serializer = ProductListSerializer(
            products, many=True, context={"request": request}
        )
        return APIResponse.success(
            data={
                "brand": BrandSerializer(brand, context={"request": request}).data,
                "products": serializer.data,
            }
        )


class ProductImageSetPrimaryView(APIView):
    """Set a specific image as primary, clearing any existing primary."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, image_id):
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return APIResponse.error(message="Product not found", status_code=404)

        try:
            image = ProductImage.objects.get(pk=image_id, product=product)
        except ProductImage.DoesNotExist:
            return APIResponse.error(message="Image not found", status_code=404)

        # Clear existing primary then set new one
        ProductImage.objects.filter(product=product, is_primary=True).update(
            is_primary=False
        )
        image.is_primary = True
        image.save()

        serializer = ProductImageSerializer(image, context={"request": request})
        return APIResponse.success(
            data=serializer.data, message="Primary image updated successfully"
        )
