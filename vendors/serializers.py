from rest_framework import serializers

from catalog.serializers import CategorySerializer
from markets.serializers import MarketSerializer

from .models import Vendor


class VendorListSerializer(serializers.ModelSerializer):
    market_detail = MarketSerializer(source="market", read_only=True)
    category_detail = CategorySerializer(source="primary_category", read_only=True)
    owner_email = serializers.EmailField(source="user.email", read_only=True)
    cover = serializers.ReadOnlyField()

    class Meta:
        model = Vendor
        fields = [
            "id", "shop_name", "market", "market_detail",
            "primary_category", "category_detail", "owner_email",
            "description", "phone", "image", "image_url", "cover",
            "is_verified", "avg_rating", "ratings_count",
        ]
        read_only_fields = ["is_verified", "avg_rating", "ratings_count"]


class VendorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id", "shop_name", "market", "primary_category",
            "description", "phone", "image", "image_url",
        ]


class VendorVerifySerializer(serializers.Serializer):
    is_verified = serializers.BooleanField()
