import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("mandiconnect")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "snapshot-prices-nightly": {
        "task": "pricing.tasks.snapshot_active_prices",
        "schedule": crontab(hour=0, minute=30),
    },
    "expire-stale-listings": {
        "task": "pricing.tasks.expire_stale_listings",
        "schedule": crontab(hour=1, minute=0),
    },
    "recompute-vendor-ratings": {
        "task": "reviews.tasks.recompute_vendor_ratings",
        "schedule": crontab(hour=2, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
