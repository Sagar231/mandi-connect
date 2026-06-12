from rest_framework.routers import DefaultRouter

from .views import MarketViewSet

router = DefaultRouter()
router.register("markets", MarketViewSet, basename="market")

urlpatterns = router.urls
