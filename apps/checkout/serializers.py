from rest_framework import serializers
from .models import Order, OrderItem
from apps.user.serializers import UserProfileSerializer


# Order item serializer
class OrderItemSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "product_slug",
            "product_image",
            "unit",
            "price",
            "discounted_price",
            "quantity",
            "delivery_date",
        ]

    def get_product_image(self, obj):
        request = self.context.get("request")
        if obj.product_image and request:
            return request.build_absolute_uri(obj.product_image)
        return obj.product_image


# Order serializer for user list and detail
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "user",
            "status",
            "reject_note",
            "total_amount",
            "items",
            "created_at",
        ]


# Order serializer for admin list and detail, includes full user info
class AdminOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserProfileSerializer(read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "user",
            "item_count",
            "status",
            "reject_note",
            "company",
            "company_address",
            "total_amount",
            "items",
            "created_at",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


# Order status update serializer for admin
class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["accepted", "rejected", "delivered"])
    reject_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["status"] == "rejected" and not attrs.get("reject_note"):
            raise serializers.ValidationError(
                "reject_note is required when rejecting an order."
            )
        return attrs
