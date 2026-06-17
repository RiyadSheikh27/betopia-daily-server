from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from apps.utils.models import TimeStampedModel


def generate_unique_slug(model_class, name, instance_id=None):
    """
    Generate a unique slug for a model instance.
    If slug exists, appends -2, -3, etc. until unique.
    Excludes the current instance when checking (for updates).
    """
    base_slug = slugify(name)
    slug = base_slug
    counter = 2

    qs = model_class.objects.filter(slug=slug)
    if instance_id:
        qs = qs.exclude(id=instance_id)

    while qs.exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        qs = model_class.objects.filter(slug=slug)
        if instance_id:
            qs = qs.exclude(id=instance_id)

    return slug


# Brand model
class Brand(TimeStampedModel):
    """Represents a product brand like Pran, Akij etc."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    icon = models.ImageField(upload_to="brands/icons/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug or (
            self.pk
            and Brand.objects.filter(pk=self.pk)
            .exclude(slug=slugify(self.name))
            .exists()
        ):
            self.slug = generate_unique_slug(Brand, self.name, self.id)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Category model
class Category(TimeStampedModel):
    """Flat single level product category."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    icon = models.ImageField(upload_to="categories/icons/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug or (
            self.pk
            and Category.objects.filter(pk=self.pk)
            .exclude(slug=slugify(self.name))
            .exists()
        ):
            self.slug = generate_unique_slug(Category, self.name, self.id)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Tag model
class Tag(TimeStampedModel):
    """Simple product tag like organic, vegan etc."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Product model
class Product(TimeStampedModel):
    """
    Core product model for the grocery e-commerce.
    discounted_price is auto calculated on save as price minus discount_amount.
    """

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        db_index=True,
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=550, unique=True, blank=True, db_index=True)
    description = CKEditor5Field(config_name="extends", blank=True, null=True)
    sku = models.CharField(
        max_length=100, unique=True, blank=True, null=True, db_index=True
    )

    # Pricing
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        db_index=True,
    )

    # Unit
    unit = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g. per kg, per liter, per piece",
    )

    # Stock
    in_stock = models.BooleanField(default=True, db_index=True)

    # Key details
    key_detail_title = models.CharField(max_length=500, blank=True, null=True)
    key_detail_description = models.TextField(blank=True, null=True)

    # Hot deal
    is_hot_deal = models.BooleanField(default=False, db_index=True)
    hot_deal_start = models.DateTimeField(blank=True, null=True)
    hot_deal_end = models.DateTimeField(blank=True, null=True)

    # Placeholder stats
    total_sold = models.PositiveIntegerField(default=100)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)

    def save(self, *args, **kwargs):
        if not self.slug or (
            self.pk
            and Product.objects.filter(pk=self.pk)
            .exclude(slug=slugify(self.name))
            .exists()
        ):
            self.slug = generate_unique_slug(Product, self.name, self.id)
        calculated = self.price - self.discount_amount
        self.discounted_price = max(calculated, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Product image model
class ProductImage(TimeStampedModel):
    """Multiple images per product."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", db_index=True
    )
    image = models.ImageField(upload_to="products/images/")
    is_primary = models.BooleanField(default=False)

    class Meta:
        # Enforce only one primary image per product at DB level
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_product",
            )
        ]

    def __str__(self):
        return f"Image for {self.product.name}"
