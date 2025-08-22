# api_v1/urls.py
from django.urls import path
from .views import roblox_ingest
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("roblox/ingest/", roblox_ingest, name="roblox_ingest"),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
]
