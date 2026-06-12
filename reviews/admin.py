from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["vendor", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["vendor__shop_name", "user__email"]
