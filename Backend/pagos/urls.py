from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoPagoViewSet,
    PagoViewSet,
    DetallePagoViewSet,
    HistorialPagoViewSet,
    TipoPlanViewSet,
    PlanViewSet,
    TransaccionStripeViewSet,
    CrearSesionStripeView,
    ConfirmarPagoStripeView,
    ContratosParaPagoView,
    stripe_webhook,
    ConfiguracionSistemaViewSet,
    ReportesAPIView,
)

router = DefaultRouter()
router.register(r'tipos-pago', TipoPagoViewSet)
router.register(r'lista', PagoViewSet)
router.register(r'detalles', DetallePagoViewSet)
router.register(r'historial', HistorialPagoViewSet)
router.register(r'tipos-plan', TipoPlanViewSet)
router.register(r'planes', PlanViewSet)
router.register(r'transacciones', TransaccionStripeViewSet, basename='transacciones')
router.register(r'configuracion', ConfiguracionSistemaViewSet, basename='configuracion-sistema')

router.register(r'panel/lista', PagoViewSet, basename='panel-pagos')
router.register(r'panel/historial', HistorialPagoViewSet, basename='panel-historial')
router.register(r'panel/transacciones', TransaccionStripeViewSet, basename='panel-transacciones')

urlpatterns = [
    path('', include(router.urls)),
    # ─── Stripe endpoints ───────────────────────────────────────
    path('stripe/crear-sesion/', CrearSesionStripeView.as_view(), name='stripe-crear-sesion'),
    path('stripe/confirmar/', ConfirmarPagoStripeView.as_view(), name='stripe-confirmar'),
    path('stripe/contratos/', ContratosParaPagoView.as_view(), name='stripe-contratos'),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    
    # ─── Reportes ──────────────────────────────────────────────
    path('reportes/', ReportesAPIView.as_view(), name='reportes'),
]
