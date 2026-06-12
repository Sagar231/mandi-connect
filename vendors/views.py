from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import IsAdminRole, IsVendorRole

from .models import Vendor
from .serializers import VendorListSerializer, VendorVerifySerializer, VendorWriteSerializer


class VendorViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["market", "is_verified"]
    search_fields = ["shop_name", "description"]
    ordering_fields = ["shop_name", "avg_rating", "created_at"]

    def get_queryset(self):
        qs = Vendor.objects.select_related("market", "user")
        user = self.request.user
        # Public: only verified vendors. Admins & the vendor themselves see all.
        if user.is_authenticated and user.is_admin_role:
            return qs
        if user.is_authenticated and user.is_vendor:
            return qs.filter(Q(is_verified=True) | Q(user=user))
        return qs.filter(is_verified=True)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return VendorWriteSerializer
        return VendorListSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsVendorRole()]
        if self.action in ("verify", "destroy"):
            return [IsAdminRole()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        vendor = Vendor.objects.filter(user=request.user).first()
        if not vendor:
            return Response({"detail": "No vendor profile."}, status=404)
        return Response(VendorListSerializer(vendor).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminRole])
    def verify(self, request, pk=None):
        vendor = self.get_object()
        serializer = VendorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor.is_verified = serializer.validated_data["is_verified"]
        vendor.save(update_fields=["is_verified", "updated_at"])
        return Response(VendorListSerializer(vendor).data)

    @action(detail=False, methods=["get"], permission_classes=[IsVendorRole])
    def dashboard_stats(self, request):
        from pricing.models import PriceListing

        vendor = Vendor.objects.filter(user=request.user).first()
        if not vendor:
            return Response({"detail": "No vendor profile."}, status=404)
        listings = PriceListing.objects.filter(vendor=vendor)
        active = listings.filter(is_active=True)
        stock_breakdown = dict(
            active.values("stock_status").annotate(n=Count("id")).values_list("stock_status", "n")
        )
        return Response(
            {
                "shop_name": vendor.shop_name,
                "is_verified": vendor.is_verified,
                "avg_rating": vendor.avg_rating,
                "ratings_count": vendor.ratings_count,
                "total_listings": listings.count(),
                "active_listings": active.count(),
                "stock_breakdown": stock_breakdown,
                "as_of": timezone.now(),
            }
        )
