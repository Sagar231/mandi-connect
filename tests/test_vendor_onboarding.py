import pytest
from django.contrib.auth import get_user_model

from vendors.models import Vendor

User = get_user_model()


@pytest.mark.django_db
def test_vendor_registration_creates_pending_shop(api, market):
    from catalog.models import Category

    cat = Category.objects.create(name="Vegetables")
    r = api.post(
        "/api/auth/register/vendor/",
        {
            "email": "shop@test.com", "password": "Str0ngP!23", "password2": "Str0ngP!23",
            "shop_name": "Sharma Sabzi", "market": market.id, "primary_category": cat.id,
            "phone": "+91999", "description": "Fresh veggies",
        },
        format="json",
    )
    assert r.status_code == 201, r.content
    user = User.objects.get(email="shop@test.com")
    assert user.role == "vendor"
    vendor = Vendor.objects.get(user=user)
    assert vendor.is_verified is False          # pending verification
    assert vendor.shop_name == "Sharma Sabzi"
    assert vendor.primary_category_id == cat.id


@pytest.mark.django_db
def test_vendor_registration_password_mismatch(api, market):
    r = api.post(
        "/api/auth/register/vendor/",
        {"email": "x@test.com", "password": "Str0ngP!23", "password2": "nope",
         "shop_name": "X", "market": market.id},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_vendor_registration_bad_market(api):
    r = api.post(
        "/api/auth/register/vendor/",
        {"email": "x@test.com", "password": "Str0ngP!23", "password2": "Str0ngP!23",
         "shop_name": "X", "market": 9999},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_pending_vendor_hidden_from_public_list(api, market):
    u = User.objects.create_user("v@t.com", "pass12345", role="vendor")
    Vendor.objects.create(user=u, shop_name="Hidden", market=market, is_verified=False)
    r = api.get("/api/vendors/")
    rows = r.data["results"] if isinstance(r.data, dict) and "results" in r.data else r.data
    names = [v["shop_name"] for v in rows]
    assert "Hidden" not in names


@pytest.mark.django_db
def test_login_routes_role(api, verified_vendor):
    r = api.post("/api/auth/login/", {"email": "vend@test.com", "password": "pass12345"}, format="json")
    assert r.status_code == 200
    assert r.data["user"]["role"] == "vendor"
    assert r.data["user"]["has_vendor_profile"] is True
