from celery import shared_task
from django.db.models import Avg, Count


@shared_task
def recompute_single_vendor_rating(vendor_id):
    from vendors.models import Vendor

    from .models import Review

    agg = Review.objects.filter(vendor_id=vendor_id).aggregate(
        avg=Avg("rating"), n=Count("id")
    )
    Vendor.objects.filter(pk=vendor_id).update(
        avg_rating=round(agg["avg"] or 0, 2), ratings_count=agg["n"] or 0
    )
    return {"vendor": vendor_id, "avg": agg["avg"], "count": agg["n"]}


@shared_task
def recompute_vendor_ratings():
    """Scheduled full recompute across all vendors."""
    from vendors.models import Vendor

    from .models import Review

    updated = 0
    for vendor in Vendor.objects.all().iterator():
        agg = Review.objects.filter(vendor=vendor).aggregate(avg=Avg("rating"), n=Count("id"))
        vendor.avg_rating = round(agg["avg"] or 0, 2)
        vendor.ratings_count = agg["n"] or 0
        vendor.save(update_fields=["avg_rating", "ratings_count", "updated_at"])
        updated += 1
    return {"vendors_updated": updated}
