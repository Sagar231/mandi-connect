from django.urls import path

from .views import (
    AlertsPageView,
    CompareView,
    FavoritesPageView,
    HomeView,
    LoginPageView,
    MarketDetailView,
    PasswordResetPageView,
    RegisterPageView,
    SellPageView,
    VendorDashboardView,
    VendorProfileView,
    VerifyEmailPageView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("markets/<int:pk>/", MarketDetailView.as_view(), name="market-detail"),
    path("compare/", CompareView.as_view(), name="compare-page"),
    path("vendors/<int:pk>/", VendorProfileView.as_view(), name="vendor-profile"),
    path("login/", LoginPageView.as_view(), name="login-page"),
    path("register/", RegisterPageView.as_view(), name="register-page"),
    path("sell/", SellPageView.as_view(), name="sell-page"),
    path("reset-password/", PasswordResetPageView.as_view(), name="reset-page"),
    path("verify-email/", VerifyEmailPageView.as_view(), name="verify-page"),
    path("favorites/", FavoritesPageView.as_view(), name="favorites-page"),
    path("alerts/", AlertsPageView.as_view(), name="alerts-page"),
    path("dashboard/", VendorDashboardView.as_view(), name="vendor-dashboard"),
]
