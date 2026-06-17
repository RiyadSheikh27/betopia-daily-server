from rest_framework import serializers
from .models import Cart, CartItem


# Cart item serializer
class CartItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name", read_only=True)
    slug = serializers.CharField(source="product.slug", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)
    price = serializers.DecimalField(
        source="product.discounted_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    original_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    image = serializers.SerializerMethodField()
    quantity_wise_price = serializers.SerializerMethodField()
    item_discount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "name",
            "slug",
            "unit",
            "image",
            "price",
            "original_price",
            "quantity",
            "quantity_wise_price",
            "item_discount",
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        images = obj.product.images.all()
        primary = next((img for img in images if img.is_primary), None)
        image = primary or (images[0] if images else None)
        if image and request:
            return request.build_absolute_uri(image.image.url)
        return None

    def get_quantity_wise_price(self, obj):
        return round(obj.product.discounted_price * obj.quantity, 2)

    def get_item_discount(self, obj):
        return round(obj.product.discount_amount * obj.quantity, 2)


# Cart serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "subtotal",
            "total_discount",
        ]

    def get_subtotal(self, obj):
        # Original price total before discount
        return round(
            sum(item.product.price * item.quantity for item in obj.items.all()), 2
        )

    def get_total_discount(self, obj):
        return round(
            sum(
                item.product.discount_amount * item.quantity for item in obj.items.all()
            ),
            2,
        )
