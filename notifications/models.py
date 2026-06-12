from django.conf import settings
from django.db import models

from catalog.models import Product
from common.models import TimeStampedModel
from vendors.models import Vendor


class Favorite(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="favorited_by", null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="favorited_by", null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                condition=models.Q(product__isnull=False),
                name="uniq_user_product_fav",
            ),
            models.UniqueConstraint(
                fields=["user", "vendor"],
                condition=models.Q(vendor__isnull=False),
                name="uniq_user_vendor_fav",
            ),
        ]

    def __str__(self):
        target = self.product or self.vendor
        return f"{self.user} ♥ {target}"


class PriceAlert(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="price_alerts"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_alerts")
    threshold = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user}: {self.product} <= {self.threshold}"
