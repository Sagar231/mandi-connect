from rest_framework import serializers

from catalog.serializers import ProductSerializer
from vendors.serializers import VendorListSerializer

from .models import Favorite, PriceAlert


class FavoriteSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)
    vendor_detail = VendorListSerializer(source="vendor", read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "product", "vendor", "product_detail", "vendor_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if not attrs.get("product") and not attrs.get("vendor"):
            raise serializers.ValidationError("Provide a product or a vendor to favorite.")
        return attrs


class PriceAlertSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = PriceAlert
        fields = [
            "id",
            "product",
            "product_detail",
            "threshold",
            "is_active",
            "last_triggered_at",
            "created_at",
        ]
        read_only_fields = ["id", "last_triggered_at", "created_at"]
