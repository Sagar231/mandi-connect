from django.contrib import admin

from .models import Favorite, PriceAlert


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "vendor", "created_at"]
    search_fields = ["user__email"]


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "threshold", "is_active", "last_triggered_at"]
    list_filter = ["is_active"]
    search_fields = ["user__email", "product__name"]
