from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

api_patterns = [
    path("auth/", include("users.urls")),
    path("", include("markets.urls")),
    path("", include("catalog.urls")),
    path("", include("pricing.urls")),
    path("", include("vendors.urls")),
    path("", include("reviews.urls")),
    path("", include("notifications.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/", include((api_patterns, "api"))),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Frontend (server-rendered templates)
    path("", include("frontend.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
