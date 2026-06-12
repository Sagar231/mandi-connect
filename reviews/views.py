from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from common.permissions import IsOwnerOrReadOnly

from .models import Review
from .serializers import ReviewSerializer
from .tasks import recompute_single_vendor_rating


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.select_related("user", "vendor")
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["vendor", "rating"]

    def perform_create(self, serializer):
        if Review.objects.filter(
            vendor=serializer.validated_data["vendor"], user=self.request.user
        ).exists():
            raise ValidationError("You have already reviewed this vendor.")
        review = serializer.save(user=self.request.user)
        recompute_single_vendor_rating.delay(review.vendor_id)

    def perform_update(self, serializer):
        review = serializer.save()
        recompute_single_vendor_rating.delay(review.vendor_id)

    def perform_destroy(self, instance):
        vendor_id = instance.vendor_id
        instance.delete()
        recompute_single_vendor_rating.delay(vendor_id)
