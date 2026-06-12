from django.db import models

from common.models import SoftDeleteModel


class Market(SoftDeleteModel):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    opening_hours = models.CharField(max_length=120, blank=True, help_text="e.g. 6:00 AM - 9:00 PM")
    image = models.ImageField(upload_to="markets/", null=True, blank=True)
    image_url = models.URLField(blank=True, help_text="External image URL (used when no file uploaded)")

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["city"]), models.Index(fields=["name"])]

    def __str__(self):
        return f"{self.name} ({self.city})"

    @property
    def cover(self):
        if self.image:
            return self.image.url
        return self.image_url or ""
