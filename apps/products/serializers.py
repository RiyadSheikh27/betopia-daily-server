from rest_framework import serializers
from .models import Brand, Category, Tag, Product, ProductImage


# Brand serializers
class BrandSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "icon", "product_count"]
        read_only_fields = ["slug"]

    def get_icon(self, obj):
        request = self.context.get("request")
        if obj.icon and request:
            return request.build_absolute_uri(obj.icon.url)
        return None


# Category serializers
class CategorySerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "product_count"]
        read_only_fields = ["slug"]

    def get_icon(self, obj):
        request = self.context.get("request")
        if obj.icon and request:
            return request.build_absolute_uri(obj.icon.url)
        return None


# Tag serializers
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


# Product image serializer
class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# Product list serializer (lightweight for listing)
class ProductListSerializer(serializers.ModelSerializer):
    first_image = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    brand_slug = serializers.CharField(source="brand.slug", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "discount_amount",
            "discounted_price",
            "unit",
            "first_image",
            "in_stock",
            "is_hot_deal",
            "status",
            "brand_name",
            "brand_slug",
            "category_name",
            "category_slug",
            "total_sold",
            "avg_rating",
        ]

    def get_first_image(self, obj):
        request = self.context.get("request")
        # images are prefetched, avoid extra query by iterating in Python
        images = obj.images.all()
        primary = next((img for img in images if img.is_primary), None)
        image = primary or (images[0] if images else None)
        if image and request:
            return request.build_absolute_uri(image.image.url)
        return None


# Product detail serializer (full info)
class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "sku",
            "price",
            "discount_amount",
            "discounted_price",
            "unit",
            "in_stock",
            "key_detail_title",
            "key_detail_description",
            "is_hot_deal",
            "status",
            "hot_deal_start",
            "hot_deal_end",
            "total_sold",
            "avg_rating",
            "brand",
            "category",
            "tags",
            "images",
            "created_at",
            "updated_at",
        ]


# Product create/update serializer (for CMS)
class ProductWriteSerializer(serializers.ModelSerializer):
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "brand",
            "category",
            "tag_ids",
            "name",
            "description",
            "sku",
            "price",
            "discount_amount",
            "unit",
            "in_stock",
            "key_detail_title",
            "key_detail_description",
            "is_hot_deal",
            "status",
            "hot_deal_start",
            "hot_deal_end",
        ]

    def validate(self, attrs):
        price = attrs.get("price", 0)
        discount = attrs.get("discount_amount", 0)
        if discount > price:
            raise serializers.ValidationError(
                "Discount amount cannot be greater than price."
            )
        return attrs

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        product = Product.objects.create(**validated_data)
        if tag_ids:
            product.tags.set(tag_ids)
        return product

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance
