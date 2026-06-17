from rest_framework.views import APIView

from apps.utils.custom_response import APIResponse
from apps.user.permissions import IsAuthenticated
from apps.user.utils import decode_jwt_payload, get_token_from_request
from apps.user.models import UserProfile
from apps.products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer


def get_profile(request) -> UserProfile | None:
    """Resolve UserProfile from JWT in request."""
    token = get_token_from_request(request)
    if not token:
        return None
    payload = decode_jwt_payload(token)
    if not payload:
        return None
    return UserProfile.objects.filter(uid=payload["uid"]).first()


def get_or_create_cart(profile: UserProfile) -> Cart:
    """Get or create cart for a user."""
    cart, _ = Cart.objects.get_or_create(user=profile)
    return cart


# Cart view
class CartView(APIView):
    """Get the current user's cart."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)
        cart = get_or_create_cart(profile)
        serializer = CartSerializer(
            Cart.objects.prefetch_related("items__product__images").get(pk=cart.pk),
            context={"request": request},
        )
        return APIResponse.success(data=serializer.data)


# Cart item views
class CartItemAddView(APIView):
    """Add a product to the cart."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        product_slug = request.data.get("product_slug")
        if not product_slug:
            return APIResponse.error(message="product_slug is required")

        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            return APIResponse.error(message="Product not found", status_code=404)

        if not product.in_stock:
            return APIResponse.error(
                message="Cannot add this item to cart since it is not in stock"
            )

        cart = get_or_create_cart(profile)

        if CartItem.objects.filter(cart=cart, product=product).exists():
            return APIResponse.error(message="Product is already in cart")

        CartItem.objects.create(cart=cart, product=product, quantity=1)

        serializer = CartSerializer(
            Cart.objects.prefetch_related("items__product__images").get(pk=cart.pk),
            context={"request": request},
        )
        return APIResponse.success(data=serializer.data, message="Item added to cart")


class CartItemUpdateView(APIView):
    """Update quantity of a cart item."""

    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        profile = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        quantity = request.data.get("quantity")
        if quantity is None:
            return APIResponse.error(message="quantity is required")

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return APIResponse.error(message="quantity must be a valid integer")

        if quantity < 1:
            return APIResponse.error(message="quantity must be at least 1")

        try:
            cart = Cart.objects.get(user=profile)
            item = CartItem.objects.get(pk=item_id, cart=cart)
        except Cart.DoesNotExist:
            return APIResponse.error(message="Cart not found", status_code=404)
        except CartItem.DoesNotExist:
            return APIResponse.error(message="Cart item not found", status_code=404)

        item.quantity = quantity
        item.save()

        serializer = CartSerializer(
            Cart.objects.prefetch_related("items__product__images").get(pk=cart.pk),
            context={"request": request},
        )
        return APIResponse.success(data=serializer.data, message="Quantity updated")


class CartItemDeleteView(APIView):
    """Remove a single item from the cart."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        profile = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        try:
            cart = Cart.objects.get(user=profile)
            item = CartItem.objects.get(pk=item_id, cart=cart)
        except Cart.DoesNotExist:
            return APIResponse.error(message="Cart not found", status_code=404)
        except CartItem.DoesNotExist:
            return APIResponse.error(message="Cart item not found", status_code=404)

        item.delete()

        serializer = CartSerializer(
            Cart.objects.prefetch_related("items__product__images").get(pk=cart.pk),
            context={"request": request},
        )
        return APIResponse.success(
            data=serializer.data, message="Item removed from cart"
        )


class CartClearView(APIView):
    """Clear all items from the cart."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        profile = get_profile(request)
        if not profile:
            return APIResponse.error(message="User profile not found", status_code=404)

        try:
            cart = Cart.objects.get(user=profile)
        except Cart.DoesNotExist:
            return APIResponse.error(message="Cart not found", status_code=404)

        cart.items.all().delete()
        return APIResponse.success(message="Cart cleared")
