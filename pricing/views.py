from datetime import timedelta

from django.core.cache import cache
from django.db.models import Avg, Max, Min
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsVendorOwnerOrReadOnly
from notifications.tasks import check_price_alerts

from .models import PriceHistory, PriceListing
from .serializers import (
    ComparisonRowSerializer,
    PriceListingReadSerializer,
    PriceListingWriteSerializer,
    TrendPointSerializer,
)

COMPARE_CACHE_TTL = 60 * 5
TREND_CACHE_TTL = 60 * 10


class PriceListingViewSet(viewsets.ModelViewSet):
    queryset = PriceListing.objects.select_related(
        "vendor", "product", "vendor__market"
    ).filter(vendor__is_verified=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "product": ["exact"],
        "vendor": ["exact"],
        "vendor__market": ["exact"],
        "product__category": ["exact"],
        "stock_status": ["exact"],
        "price": ["gte", "lte"],
        "date": ["exact", "gte", "lte"],
    }
    search_fields = ["product__name", "vendor__shop_name"]
    ordering_fields = ["price", "date"]
    permission_classes = [IsAuthenticatedOrReadOnly, IsVendorOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PriceListingWriteSerializer
        return PriceListingReadSerializer

    def _vendor(self):
        vendor = getattr(self.request.user, "vendor_profile", None)
        if not vendor:
            raise PermissionDenied("Only vendors with a profile can manage listings.")
        if not vendor.is_verified:
            raise PermissionDenied("Your vendor account is not yet verified by an admin.")
        return vendor

    def perform_create(self, serializer):
        listing = serializer.save(vendor=self._vendor())
        check_price_alerts.delay(listing.product_id, str(listing.price))

    def perform_update(self, serializer):
        listing = serializer.save()
        check_price_alerts.delay(listing.product_id, str(listing.price))


class CheapestVendorView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        parameters=[OpenApiParameter("product", int, required=True),
                    OpenApiParameter("market", int, required=False)],
        responses=ComparisonRowSerializer(many=True),
    )
    def get(self, request):
        product_id = request.query_params.get("product")
        if not product_id:
            raise ValidationError({"product": "This query param is required."})
        market_id = request.query_params.get("market")
        cache_key = f"compare:{product_id}:{market_id or 'all'}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        qs = (
            PriceListing.objects.filter(
                product_id=product_id, is_active=True, vendor__is_verified=True
            )
            .select_related("vendor", "vendor__market")
            .order_by("price")
        )
        if market_id:
            qs = qs.filter(vendor__market_id=market_id)
        rows = [
            {
                "vendor_id": l.vendor_id,
                "shop_name": l.vendor.shop_name,
                "market": l.vendor.market.name,
                "price": l.price,
                "stock_status": l.stock_status,
                "avg_rating": l.vendor.avg_rating,
            }
            for l in qs
        ]
        data = ComparisonRowSerializer(rows, many=True).data
        cache.set(cache_key, data, COMPARE_CACHE_TTL)
        return Response(data)


class PriceTrendView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        parameters=[OpenApiParameter("product", int, required=True),
                    OpenApiParameter("days", int, required=False)],
        responses=TrendPointSerializer(many=True),
    )
    def get(self, request):
        product_id = request.query_params.get("product")
        if not product_id:
            raise ValidationError({"product": "This query param is required."})
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            raise ValidationError({"days": "Must be an integer."})
        days = max(1, min(days, 365))
        cache_key = f"trend:{product_id}:{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        since = timezone.localdate() - timedelta(days=days)
        points = (
            PriceHistory.objects.filter(product_id=product_id, date__gte=since)
            .values("date")
            .annotate(min_price=Min("price"), avg_price=Avg("price"), max_price=Max("price"))
            .order_by("date")
        )
        data = TrendPointSerializer(list(points), many=True).data
        cache.set(cache_key, data, TREND_CACHE_TTL)
        return Response(data)
