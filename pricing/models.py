from django.db import models
from django.utils import timezone

from catalog.models import Product
from common.models import SoftDeleteModel, TimeStampedModel
from vendors.models import Vendor


class PriceListing(SoftDeleteModel):
    """The core entity: a vendor's current price for a product."""

    class Stock(models.TextChoices):
        IN_STOCK = "in_stock", "In stock"
        LOW = "low", "Low stock"
        OUT = "out", "Out of stock"

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="listings")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="listings")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_status = models.CharField(max_length=10, choices=Stock.choices, default=Stock.IN_STOCK)
    date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date", "price"]
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "product", "date"],
                condition=models.Q(is_deleted=False),
                name="uniq_vendor_product_per_day",
            )
        ]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["vendor", "date"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.product} @ {self.vendor}: {self.price}"


class PriceHistory(TimeStampedModel):
    """Immutable daily snapshots used for trend charts."""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="price_history")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    class Meta:
        ordering = ["-date"]
        unique_together = ("vendor", "product", "date")
        indexes = [models.Index(fields=["product", "date"])]

    def __str__(self):
        return f"{self.product} {self.date}: {self.price}"
