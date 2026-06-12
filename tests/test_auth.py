import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_register_and_login(api):
    r = api.post("/api/auth/register/", {
        "email": "new@test.com", "password": "Str0ngPass!23", "password2": "Str0ngPass!23",
        "role": "customer",
    }, format="json")
    assert r.status_code == 201, r.content
    assert User.objects.filter(email="new@test.com").exists()

    r = api.post("/api/auth/login/", {"email": "new@test.com", "password": "Str0ngPass!23"}, format="json")
    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data
    assert r.data["user"]["role"] == "customer"


@pytest.mark.django_db
def test_register_password_mismatch(api):
    r = api.post("/api/auth/register/", {
        "email": "x@test.com", "password": "Str0ngPass!23", "password2": "different",
    }, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_logout_blacklists_refresh(api, customer):
    r = api.post("/api/auth/login/", {"email": "cust@test.com", "password": "pass12345"}, format="json")
    refresh = r.data["refresh"]
    api.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
    out = api.post("/api/auth/logout/", {"refresh": refresh}, format="json")
    assert out.status_code == 205
    # blacklisted refresh can no longer be used
    again = api.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
    assert again.status_code == 401
