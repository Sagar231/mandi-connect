import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Category, Product
from markets.models import Market
from vendors.models import Vendor

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user("cust@test.com", "pass12345", role="customer", is_email_verified=True)


@pytest.fixture
def vendor_user(db):
    return User.objects.create_user("vend@test.com", "pass12345", role="vendor", is_email_verified=True)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser("admin@test.com", "pass12345")


@pytest.fixture
def market(db):
    return Market.objects.create(name="Test Mandi", city="Delhi", latitude=28.7, longitude=77.1)


@pytest.fixture
def verified_vendor(db, vendor_user, market):
    return Vendor.objects.create(user=vendor_user, shop_name="Shop A", market=market, is_verified=True)


@pytest.fixture
def product(db):
    cat = Category.objects.create(name="Vegetables")
    return Product.objects.create(category=cat, name="Tomato", unit="kg")


def auth(api, user):
    api.force_authenticate(user=user)
    return api
