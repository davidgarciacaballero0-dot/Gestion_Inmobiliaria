from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UsuarioViewSet, RegistroView, AgendaViewSet,
    NotificacionViewSet, ChatViewSet, MensajeViewSet,
    BloqueoViewSet, ResenaViewSet, CustomTokenObtainPairView,
    ScoringInquilinoView, MiScoringPasaporteView,
    PasaporteInquilinoPDFView, MiPasaportePDFView
)

router = DefaultRouter()
router.register(r'lista', UsuarioViewSet)
router.register(r'registro', RegistroView, basename='registro')
router.register(r'agenda', AgendaViewSet, basename='agenda')
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'mensajes', MensajeViewSet, basename='mensaje')
router.register(r'bloqueos', BloqueoViewSet, basename='bloqueo')
router.register(r'resenas', ResenaViewSet, basename='resena')

router.register(r'panel/lista', UsuarioViewSet, basename='panel-usuarios')
router.register(r'panel/agenda', AgendaViewSet, basename='panel-agenda')
router.register(r'panel/notificaciones', NotificacionViewSet, basename='panel-notificaciones')

urlpatterns = [
    path('scoring-inquilino/<int:usuario_id>/pdf/', PasaporteInquilinoPDFView.as_view(), name='scoring-inquilino-pdf'),
    path('scoring-inquilino/<int:usuario_id>/', ScoringInquilinoView.as_view(), name='scoring-inquilino'),
    path('mi-scoring-pasaporte/pdf/', MiPasaportePDFView.as_view(), name='mi-scoring-pasaporte-pdf'),
    path('mi-scoring-pasaporte/', MiScoringPasaporteView.as_view(), name='mi-scoring-pasaporte'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]


