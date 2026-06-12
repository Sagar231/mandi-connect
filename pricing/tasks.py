from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone


@shared_task
def snapshot_active_prices():
    """Nightly: copy each active listing's current price into PriceHistory."""
    from .models import PriceHistory, PriceListing

    today = timezone.localdate()
    created = 0
    listings = PriceListing.objects.filter(is_active=True, vendor__is_verified=True)
    for listing in listings.iterator():
        _, was_created = PriceHistory.objects.update_or_create(
            vendor_id=listing.vendor_id,
            product_id=listing.product_id,
            date=today,
            defaults={"price": listing.price},
        )
        created += int(was_created)
    return {"snapshotted": listings.count(), "new_rows": created}


@shared_task
def expire_stale_listings():
    """Deactivate listings whose date is older than LISTING_STALE_DAYS."""
    from .models import PriceListing

    cutoff = timezone.localdate() - timedelta(days=int(settings.LISTING_STALE_DAYS))
    n = PriceListing.objects.filter(is_active=True, date__lt=cutoff).update(is_active=False)
    return {"deactivated": n, "cutoff": str(cutoff)}
