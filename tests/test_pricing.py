from datetime import timedelta

import pytest
from django.utils import timezone

from conftest import auth
from pricing.models import PriceHistory, PriceListing


@pytest.mark.django_db
def test_cheapest_vendor_comparison(api, market, product):
    from vendors.models import Vendor
    from django.contrib.auth import get_user_model
    U = get_user_model()
    prices = [80, 55, 70]
    for i, p in enumerate(prices):
        u = U.objects.create_user(f"v{i}@t.com", "pass12345", role="vendor")
        v = Vendor.objects.create(user=u, shop_name=f"S{i}", market=market, is_verified=True)
        PriceListing.objects.create(vendor=v, product=product, price=p)
    r = api.get(f"/api/compare/?product={product.id}")
    assert r.status_code == 200
    assert [float(row["price"]) for row in r.data] == sorted(prices)  # cheapest first
    assert float(r.data[0]["price"]) == 55


@pytest.mark.django_db
def test_compare_requires_product(api):
    r = api.get("/api/compare/")
    assert r.status_code == 400


@pytest.mark.django_db
def test_price_trend_aggregates_history(api, verified_vendor, product):
    today = timezone.localdate()
    for d in range(5):
        PriceHistory.objects.create(
            vendor=verified_vendor, product=product, price=40 + d, date=today - timedelta(days=d)
        )
    r = api.get(f"/api/price-trend/?product={product.id}&days=10")
    assert r.status_code == 200
    assert len(r.data) == 5
    assert "avg_price" in r.data[0]


@pytest.mark.django_db
def test_nearby_markets(api, market):
    r = api.get("/api/markets/nearby/?lat=28.70&lng=77.10&radius_km=20")
    assert r.status_code == 200
    assert len(r.data) == 1
    assert "distance_km" in r.data[0]
