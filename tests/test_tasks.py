import pytest
from django.utils import timezone
from datetime import timedelta

from pricing.models import PriceHistory, PriceListing
from pricing.tasks import expire_stale_listings, snapshot_active_prices
from reviews.models import Review
from reviews.tasks import recompute_vendor_ratings


@pytest.mark.django_db
def test_snapshot_creates_history(verified_vendor, product):
    PriceListing.objects.create(vendor=verified_vendor, product=product, price=42)
    result = snapshot_active_prices()
    assert result["snapshotted"] == 1
    assert PriceHistory.objects.filter(product=product).count() == 1


@pytest.mark.django_db
def test_expire_stale_listings(verified_vendor, product):
    old = PriceListing.objects.create(vendor=verified_vendor, product=product, price=10)
    PriceListing.objects.filter(pk=old.pk).update(date=timezone.localdate() - timedelta(days=10))
    expire_stale_listings()
    old.refresh_from_db()
    assert old.is_active is False


@pytest.mark.django_db
def test_recompute_ratings(verified_vendor, customer):
    Review.objects.create(vendor=verified_vendor, user=customer, rating=4)
    recompute_vendor_ratings()
    verified_vendor.refresh_from_db()
    assert verified_vendor.ratings_count == 1
    assert float(verified_vendor.avg_rating) == 4.0
