from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    EmailVerifyView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    VendorRegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/vendor/", VendorRegisterView.as_view(), name="register_vendor"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("verify-email/", EmailVerifyView.as_view(), name="verify_email"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
