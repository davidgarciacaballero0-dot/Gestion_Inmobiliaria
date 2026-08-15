"""
URL configuration for Autogestión Inmobiliaria.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from usuarios.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ─── JWT Authentication ─────────────────────────────────────
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ─── API Routes ─────────────────────────────────────────────
    path('api/usuarios/', include('usuarios.urls')),
    path('api/inmuebles/', include('inmuebles.urls')),
    path('api/pagos/', include('pagos.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
