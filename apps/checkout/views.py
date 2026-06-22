from django.db import transaction
from django.db.models import Sum, Q
from rest_framework.views import APIView

from apps.utils.custom_response import APIResponse
from apps.utils.pagination import StandardPagination
from apps.user.permissions import IsAuthenticated
from apps.user.utils import decode_jwt_payload, get_token_from_request
from apps.user.models import UserProfile
from apps.cart.models import Cart
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    AdminOrderSerializer,
    OrderStatusUpdateSerializer,
)
from .utils import (
    get_eligible_amount,
    post_grocery_order,
    confirm_order_delivery,
)


def get_profile(request) -> UserProfile | None:
    """Resolve UserProfile from JWT in request, also returns the raw access token."""
    token = get_token_from_request(request)
    if not token:
        return None, None
    payload = decode_jwt_payload(token)
    if not payload:
        return None, None
    profile = UserProfile.objects.filter(uid=payload["uid"]).first()
    return profile, token


def get_pending_accepted_total(user):
    """Sum of all pending and accepted order amounts for a user."""
    total = Order.objects.filter(
        user=user, status__in=["pending", "accepted"]
    ).aggregate(total=Sum("total_amount"))["total"]
    return total or 0


# Place order and list own orders
class OrderListCreateView(APIView):
    """List user's own orders, or place a new order from cart."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        orders = (
            Order.objects.filter(user=profile)
            .select_related("user")
            .prefetch_related("items")
            .order_by("-created_at")
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(page, many=True, context={"request": request})
        return APIResponse.paginated(
            data=serializer.data, pagination_meta=paginator.get_paginated_meta()
        )

    def post(self, request):
        profile, token = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        cart = (
            Cart.objects.filter(user=profile).prefetch_related("items__product").first()
        )
        if not cart or not cart.items.exists():
            return APIResponse.error(message="Cart is empty")

        # Check stock validity for all items before placing the order
        for item in cart.items.all():
            if not item.product.in_stock:
                return APIResponse.error(message=f"{item.product.name} is out of stock")

        order_total = sum(
            item.product.discounted_price * item.quantity for item in cart.items.all()
        )

        # Step 1: check eligibility by email, block order entirely on failure
        eligible_amount = get_eligible_amount(profile.email)
        if eligible_amount is None:
            return APIResponse.error(
                message="Unable to verify eligibility balance. Please try again later.",
                status_code=503,
            )

        # Step 2: check sum of existing pending + accepted orders plus this new order
        existing_total = get_pending_accepted_total(profile)
        if existing_total + order_total > eligible_amount:
            return APIResponse.error(
                message="Order amount exceeds your eligible balance",
                status_code=400,
            )

        # Step 3: create order and snapshot items
        product_names = ", ".join(item.product.name for item in cart.items.all())

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=profile,
                    company=profile.company,
                    company_address=getattr(profile, "company_address", None),
                    total_amount=order_total,
                )

                for item in cart.items.all():
                    product = item.product
                    images = product.images.all()
                    primary = next((img for img in images if img.is_primary), None)
                    image = primary or (images[0] if images else None)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        product_slug=product.slug,
                        product_image=image.image.url if image else None,
                        unit=product.unit,
                        price=product.price,
                        discounted_price=product.discounted_price,
                        quantity=item.quantity,
                        delivery_date=product.delivery_date,
                    )

                success = post_grocery_order(
                    email=profile.email,
                    amount=order_total,
                    product_name=product_names,
                    order_id=order.order_id,
                    funding_source="bank",
                )
                if not success:
                    raise ValueError("External grocery order submission failed")

                # Step 4: confirm the order to deduct money from central system
                confirm_success = confirm_order_delivery(order.order_id)
                if not confirm_success:
                    raise ValueError("Failed to confirm order with central system")
        except ValueError:
            return APIResponse.error(
                message="Unable to submit order to the external grocery system. Please try again later.",
                status_code=503,
            )

        # Clear cart after successful order placement
        cart.items.all().delete()

        serializer = OrderSerializer(order, context={"request": request})
        return APIResponse.success(
            data=serializer.data, message="Order placed successfully"
        )


# Single order detail for the user
class OrderDetailView(APIView):
    """Get a single order belonging to the requesting user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        profile, _ = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        try:
            order = (
                Order.objects.select_related("user")
                .prefetch_related("items")
                .get(order_id=order_id, user=profile)
            )

        except Order.DoesNotExist:
            return APIResponse.error(message="Order not found", status_code=404)

        serializer = OrderSerializer(order, context={"request": request})
        return APIResponse.success(data=serializer.data)


# Admin order list
class AdminOrderListView(APIView):
    """List all orders. Admin only. Supports status and company filters."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = get_profile(request)
        if not profile or profile.role != "admin":
            return APIResponse.error(message="Admin access required", status_code=403)

        orders = (
            Order.objects.select_related("user")
            .prefetch_related("items")
            .order_by("-created_at")
        )

        status_filter = request.query_params.get("status")
        company_filter = request.query_params.get("company")

        if status_filter:
            orders = orders.filter(status=status_filter)
        if company_filter:
            orders = orders.filter(company__icontains=company_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(orders, request)
        serializer = AdminOrderSerializer(page, many=True, context={"request": request})
        return APIResponse.paginated(
            data=serializer.data, pagination_meta=paginator.get_paginated_meta()
        )


# Admin order detail and status update
class AdminOrderDetailView(APIView):
    """Get order detail or update status. Admin only."""

    permission_classes = [IsAuthenticated]

    def get_order(self, order_id):
        try:
            return (
                Order.objects.select_related("user")
                .prefetch_related("items")
                .get(order_id=order_id)
            )
        except Order.DoesNotExist:
            return None

    def get(self, request, order_id):
        profile, _ = get_profile(request)
        if not profile or profile.role != "admin":
            return APIResponse.error(message="Admin access required", status_code=403)

        order = self.get_order(order_id)
        if not order:
            return APIResponse.error(message="Order not found", status_code=404)

        serializer = AdminOrderSerializer(order, context={"request": request})
        return APIResponse.success(data=serializer.data)

    def patch(self, request, order_id):
        profile, token = get_profile(request)
        if not profile or profile.role != "admin":
            return APIResponse.error(message="Admin access required", status_code=403)

        order = self.get_order(order_id)
        if not order:
            return APIResponse.error(message="Order not found", status_code=404)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.error(errors=serializer.errors)

        new_status = serializer.validated_data["status"]

        # Reject transition: from pending only
        if new_status == "rejected":
            if order.status != "pending":
                return APIResponse.error(message="Only pending orders can be rejected")
            order.status = "rejected"
            order.reject_note = serializer.validated_data["reject_note"]
            order.save()
            return APIResponse.success(
                data=AdminOrderSerializer(order, context={"request": request}).data,
                message="Order rejected",
            )

        # Delivered transition: from accepted only
        if new_status == "delivered":
            if order.status != "accepted":
                return APIResponse.error(
                    message="Only accepted orders can be marked as delivered"
                )
            success = confirm_order_delivery(order.order_id)
            if not success:
                return APIResponse.error(
                    message="Failed to confirm delivery with central system",
                    status_code=503,
                )
            order.status = "delivered"
            order.save()
            return APIResponse.success(
                data=AdminOrderSerializer(order, context={"request": request}).data,
                message="Order marked as delivered",
            )

        # Accept transition: from pending only
        if order.status != "pending":
            return APIResponse.error(message="Only pending orders can be accepted")

        order.status = "accepted"
        order.save()
        return APIResponse.success(
            data=AdminOrderSerializer(order, context={"request": request}).data,
            message="Order accepted",
        )
