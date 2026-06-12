from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "image_url"]
        read_only_fields = ["slug"]


class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    cover = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "unit", "unit_display",
            "category", "category_detail", "description",
            "image", "image_url", "cover",
        ]
        read_only_fields = ["slug"]
