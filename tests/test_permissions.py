import pytest

from conftest import auth


@pytest.mark.django_db
def test_anonymous_can_read_markets(api, market):
    r = api.get("/api/markets/")
    assert r.status_code == 200


@pytest.mark.django_db
def test_only_admin_creates_market(api, customer, admin_user):
    payload = {"name": "New", "city": "Pune"}
    r = auth(api, customer).post("/api/markets/", payload, format="json")
    assert r.status_code == 403
    api.force_authenticate(user=None)
    r = auth(api, admin_user).post("/api/markets/", payload, format="json")
    assert r.status_code == 201


@pytest.mark.django_db
def test_unverified_vendor_cannot_create_listing(api, vendor_user, market, product):
    from vendors.models import Vendor
    Vendor.objects.create(user=vendor_user, shop_name="Pending", market=market, is_verified=False)
    r = auth(api, vendor_user).post("/api/price-listings/", {"product": product.id, "price": 50}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_verified_vendor_creates_listing(api, verified_vendor, product):
    r = auth(api, verified_vendor.user).post(
        "/api/price-listings/", {"product": product.id, "price": 50}, format="json"
    )
    assert r.status_code == 201, r.content
    assert r.data["price"] == "50.00"
