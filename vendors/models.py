from django.conf import settings
from django.db import models

from catalog.models import Category
from common.models import SoftDeleteModel
from markets.models import Market


class Vendor(SoftDeleteModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor_profile"
    )
    shop_name = models.CharField(max_length=150)
    market = models.ForeignKey(Market, on_delete=models.PROTECT, related_name="vendors")
    primary_category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vendors", help_text="Main goods this shop sells",
    )
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to="vendors/", null=True, blank=True)
    image_url = models.URLField(blank=True, help_text="Shop banner URL (used when no file uploaded)")
    is_verified = models.BooleanField(default=False)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    ratings_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["shop_name"]
        indexes = [models.Index(fields=["is_verified"]), models.Index(fields=["market"])]

    def __str__(self):
        return self.shop_name

    @property
    def cover(self):
        if self.image:
            return self.image.url
        return self.image_url or ""
