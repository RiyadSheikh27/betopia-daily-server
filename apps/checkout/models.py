import random
import string
from django.db import models
from apps.utils.models import TimeStampedModel
from apps.user.models import UserProfile
from apps.products.models import Product


def generate_order_id():
    """Generate a unique order id like BETOPIA_DAILY_XYZ123"""
    while True:
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        order_id = f"BETOPIA_DAILY_{suffix}"
        if not Order.objects.filter(order_id=order_id).exists():
            return order_id


class Order(TimeStampedModel):
    """Order model"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("delivered", "Delivered"),
    ]

    order_id = models.CharField(
        max_length=50, unique=True, db_index=True, editable=False
    )
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="orders", db_index=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    reject_note = models.TextField(blank=True, null=True)

    # Snapshot of user company info at order time, since company can change later
    company = models.CharField(max_length=255)
    company_address = models.CharField(max_length=500, blank=True, null=True)

    # Total amount of the order, calculated from items at order creation
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_order_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_id


class OrderItem(TimeStampedModel):
    """Order item model - snapshot of product at order time"""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    # Snapshot fields, protected from future product edits or deletion
    product_name = models.CharField(max_length=500)
    product_slug = models.SlugField(max_length=550)
    product_image = models.CharField(max_length=1000, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
