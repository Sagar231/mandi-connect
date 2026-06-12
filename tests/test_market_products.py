import pytest

from pricing.models import PriceListing


@pytest.mark.django_db
def test_market_products_price_range(api, verified_vendor, market, product):
    from django.contrib.auth import get_user_model
    from vendors.models import Vendor

    U = get_user_model()
    PriceListing.objects.create(vendor=verified_vendor, product=product, price=40)
    u2 = U.objects.create_user("v2@t.com", "pass12345", role="vendor")
    v2 = Vendor.objects.create(user=u2, shop_name="Shop B", market=market, is_verified=True)
    PriceListing.objects.create(vendor=v2, product=product, price=60)

    r = api.get(f"/api/markets/{market.id}/products/")
    assert r.status_code == 200
    assert len(r.data) == 1
    row = r.data[0]
    assert float(row["min_price"]) == 40
    assert float(row["max_price"]) == 60
    assert row["vendor_count"] == 2


@pytest.mark.django_db
def test_market_products_excludes_unverified(api, market, product):
    from django.contrib.auth import get_user_model
    from vendors.models import Vendor

    U = get_user_model()
    u = U.objects.create_user("v@t.com", "pass12345", role="vendor")
    v = Vendor.objects.create(user=u, shop_name="Pending", market=market, is_verified=False)
    PriceListing.objects.create(vendor=v, product=product, price=40)
    r = api.get(f"/api/markets/{market.id}/products/")
    assert r.data == []
