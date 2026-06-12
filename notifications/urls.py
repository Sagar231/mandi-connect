from rest_framework.routers import DefaultRouter

from .views import FavoriteViewSet, PriceAlertViewSet

router = DefaultRouter()
router.register("favorites", FavoriteViewSet, basename="favorite")
router.register("price-alerts", PriceAlertViewSet, basename="pricealert")

urlpatterns = router.urls
