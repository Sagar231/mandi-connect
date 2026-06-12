from django.contrib import admin

from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ["shop_name", "market", "is_verified", "avg_rating", "ratings_count"]
    list_filter = ["is_verified", "market"]
    search_fields = ["shop_name", "user__email"]
    actions = ["verify_vendors", "unverify_vendors"]

    @admin.action(description="Mark selected vendors as verified")
    def verify_vendors(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description="Mark selected vendors as unverified")
    def unverify_vendors(self, request, queryset):
        queryset.update(is_verified=False)
