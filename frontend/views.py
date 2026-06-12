from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home.html"


class MarketDetailView(TemplateView):
    template_name = "markets/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["market_id"] = kwargs.get("pk")
        return ctx


class CompareView(TemplateView):
    template_name = "catalog/compare.html"


class VendorProfileView(TemplateView):
    template_name = "vendors/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["vendor_id"] = kwargs.get("pk")
        return ctx


class LoginPageView(TemplateView):
    template_name = "auth/login.html"


class RegisterPageView(TemplateView):
    template_name = "auth/register.html"


class SellPageView(TemplateView):
    template_name = "auth/sell.html"


class PasswordResetPageView(TemplateView):
    template_name = "auth/reset.html"


class VerifyEmailPageView(TemplateView):
    template_name = "auth/verify.html"


class FavoritesPageView(TemplateView):
    template_name = "customer/favorites.html"


class AlertsPageView(TemplateView):
    template_name = "customer/alerts.html"


class VendorDashboardView(TemplateView):
    template_name = "vendors/dashboard.html"
