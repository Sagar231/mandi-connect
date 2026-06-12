from math import asin, cos, radians, sin, sqrt

from django.db.models import Count, Max, Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import IsAdminRole

from .models import Market
from .serializers import MarketSerializer


class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city"]
    search_fields = ["name", "city", "area"]
    ordering_fields = ["name", "city", "created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminRole()]
        return [IsAuthenticatedOrReadOnly()]

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """?lat=..&lng=..&radius_km=5 — markets within radius (Haversine)."""
        try:
            lat = float(request.query_params["lat"])
            lng = float(request.query_params["lng"])
        except (KeyError, ValueError):
            return Response({"detail": "lat and lng query params required."}, status=400)
        radius = float(request.query_params.get("radius_km", 5))
        results = []
        for m in self.get_queryset().exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            d = _haversine(lat, lng, float(m.latitude), float(m.longitude))
            if d <= radius:
                results.append((d, m))
        results.sort(key=lambda x: x[0])
        data = []
        for d, m in results:
            row = self.get_serializer(m).data
            row["distance_km"] = round(d, 2)
            data.append(row)
        return Response(data)

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """What's sold in this market: each product with its price range and vendor count."""
        from pricing.models import PriceListing

        rows = (
            PriceListing.objects.filter(
                vendor__market_id=pk, is_active=True, vendor__is_verified=True
            )
            .values(
                "product_id", "product__name", "product__unit",
                "product__image_url", "product__category__name",
            )
            .annotate(
                min_price=Min("price"), max_price=Max("price"),
                vendor_count=Count("vendor", distinct=True),
            )
            .order_by("product__name")
        )
        data = [
            {
                "product_id": r["product_id"],
                "name": r["product__name"],
                "unit": r["product__unit"],
                "category": r["product__category__name"],
                "cover": r["product__image_url"] or "",
                "min_price": r["min_price"],
                "max_price": r["max_price"],
                "vendor_count": r["vendor_count"],
            }
            for r in rows
        ]
        return Response(data)



def _haversine(lat1, lon1, lat2, lon2):
    r = 6371  # km
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))
