from django.contrib import admin

from .models import Market


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "area", "is_deleted"]
    list_filter = ["city", "is_deleted"]
    search_fields = ["name", "city", "area"]
