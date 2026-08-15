"""from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoInmuebleViewSet,
    InmuebleViewSet,
    MultimediaViewSet,
    TipoContratoViewSet,
    ContratoViewSet,
    ComisionViewSet,
    FavoritoViewSet,
)

router = DefaultRouter()
router.register(r'tipos', TipoInmuebleViewSet)
router.register(r'lista', InmuebleViewSet)
router.register(r'multimedia', MultimediaViewSet)
router.register(r'tipos-contrato', TipoContratoViewSet)
router.register(r'contratos', ContratoViewSet)
router.register(r'comisiones', ComisionViewSet)
router.register(r'favoritos', FavoritoViewSet, basename='favoritos')

# Rutas para el panel con filtrado por usuario logueado
router.register(r'panel/tipos', TipoInmuebleViewSet, basename='panel-tipos')
router.register(r'panel/lista', InmuebleViewSet, basename='panel-inmuebles')
router.register(r'panel/contratos', ContratoViewSet, basename='panel-contratos')

urlpatterns = [
    path('', include(router.urls)),
]
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoInmuebleViewSet,
    InmuebleViewSet,
    PublicacionViewSet,
    MultimediaViewSet,
    TipoContratoViewSet,
    ContratoViewSet,
    ComisionViewSet,
    FavoritoViewSet,
    CitaViewSet,
    HorarioDisponibleViewSet,
    HotspotViewSet,
    VerificacionTituloViewSet,
    AccesoRecorrido360ViewSet,
    BlockchainHistorialView,
    BlockchainStatsView,
    AIReportView,
)

router = DefaultRouter()

# ─── Rutas públicas / generales ──────────────────────────────────────────────
router.register(r'tipos',           TipoInmuebleViewSet)
router.register(r'lista',           InmuebleViewSet)
router.register(r'publicaciones',   PublicacionViewSet,     basename='publicaciones')
router.register(r'multimedia',      MultimediaViewSet)
router.register(r'tipos-contrato',  TipoContratoViewSet, basename='tipos-contrato')
router.register(r'contratos',       ContratoViewSet,     basename='contratos')
router.register(r'comisiones',      ComisionViewSet)
router.register(r'favoritos',       FavoritoViewSet,        basename='favoritos')
router.register(r'citas',           CitaViewSet,            basename='citas')
router.register(r'horarios',        HorarioDisponibleViewSet, basename='horarios')
router.register(r'hotspots',        HotspotViewSet,         basename='hotspots')
router.register(r'verificacion',    VerificacionTituloViewSet, basename='verificacion')
router.register(r'accesos-360',     AccesoRecorrido360ViewSet, basename='accesos-360')


# ─── Rutas del panel admin ────────────────────────────────────────────────────
router.register(r'panel/tipos',     TipoInmuebleViewSet,    basename='panel-tipos')
router.register(r'panel/lista',     InmuebleViewSet,        basename='panel-inmuebles')
router.register(r'panel/publicaciones', PublicacionViewSet, basename='panel-publicaciones')
router.register(r'panel/contratos', ContratoViewSet,        basename='panel-contratos')
router.register(r'panel/tipos-contrato', TipoContratoViewSet, basename='panel-tipos-contrato')
router.register(r'panel/citas',     CitaViewSet,            basename='panel-citas')
router.register(r'panel/horarios',  HorarioDisponibleViewSet, basename='panel-horarios')
router.register(r'panel/hotspots',  HotspotViewSet,         basename='panel-hotspots')

urlpatterns = [
    path('blockchain/stats/', BlockchainStatsView.as_view(), name='blockchain-stats'),
    path('blockchain/historial/<str:asset_id>/', BlockchainHistorialView.as_view(), name='blockchain-historial'),
    path('reporte-ia/', AIReportView.as_view(), name='reporte-ia'),
    path('', include(router.urls)),
]