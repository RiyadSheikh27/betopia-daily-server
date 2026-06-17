from django.db import models
from apps.utils.models import TimeStampedModel
from apps.user.models import UserProfile
from apps.products.models import Product


# Cart model - one per user
class Cart(TimeStampedModel):
    user = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="cart"
    )

    def __str__(self):
        return f"Cart of {self.user.email}"


# Cart item model
class CartItem(TimeStampedModel):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items", db_index=True
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items", db_index=True
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        # One product per cart
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_product_per_cart"
            )
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
