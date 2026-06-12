from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "vendor", "user_email", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user_email", "created_at"]
