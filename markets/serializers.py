from rest_framework import serializers

from .models import Market


class MarketSerializer(serializers.ModelSerializer):
    vendor_count = serializers.SerializerMethodField()
    cover = serializers.ReadOnlyField()

    class Meta:
        model = Market
        fields = [
            "id", "name", "city", "area", "address",
            "latitude", "longitude", "opening_hours",
            "image", "image_url", "cover", "vendor_count", "created_at",
        ]

    def get_vendor_count(self, obj):
        return obj.vendors.filter(is_verified=True).count()
