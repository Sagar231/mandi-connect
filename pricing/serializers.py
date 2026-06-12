from rest_framework import serializers

from catalog.serializers import ProductSerializer
from vendors.serializers import VendorListSerializer

from .models import PriceHistory, PriceListing


class PriceListingReadSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)
    vendor_detail = VendorListSerializer(source="vendor", read_only=True)
    stock_display = serializers.CharField(source="get_stock_status_display", read_only=True)

    class Meta:
        model = PriceListing
        fields = [
            "id", "vendor", "vendor_detail", "product", "product_detail",
            "price", "stock_status", "stock_display", "date", "is_active",
        ]


class PriceListingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceListing
        fields = ["id", "product", "price", "stock_status", "date", "is_active"]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ["id", "vendor", "product", "price", "date"]


class ComparisonRowSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    shop_name = serializers.CharField()
    market = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_status = serializers.CharField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)


class TrendPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2)
