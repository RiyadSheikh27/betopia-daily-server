from apps.utils.models import TimeStampedModel
from django.db import models


class HeroImage(TimeStampedModel):
    """ Model to store hero images for the homepage. Each image has an order to determine its display sequence."""
    
    image = models.ImageField(upload_to="site_settings/hero/")
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Hero Image #{self.order}"