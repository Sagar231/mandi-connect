from django.contrib import admin

from .models import PriceHistory, PriceListing


@admin.register(PriceListing)
class PriceListingAdmin(admin.ModelAdmin):
    list_display = ["product", "vendor", "price", "stock_status", "date", "is_active"]
    list_filter = ["stock_status", "is_active", "date"]
    search_fields = ["product__name", "vendor__shop_name"]


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ["product", "vendor", "price", "date"]
    list_filter = ["date"]
    search_fields = ["product__name", "vendor__shop_name"]
