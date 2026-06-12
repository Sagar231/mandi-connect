from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CheapestVendorView, PriceListingViewSet, PriceTrendView

router = DefaultRouter()
router.register("price-listings", PriceListingViewSet, basename="pricelisting")

urlpatterns = [
    path("compare/", CheapestVendorView.as_view(), name="compare"),
    path("price-trend/", PriceTrendView.as_view(), name="price-trend"),
] + router.urls
