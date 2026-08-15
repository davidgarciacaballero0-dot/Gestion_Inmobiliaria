from django.contrib import admin
from .models import TipoPago, Pago, DetallePago, HistorialPago, TipoPlan, Plan, TransaccionStripe


@admin.register(TipoPago)
class TipoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']


class DetallePagoInline(admin.TabularInline):
    model = DetallePago
    extra = 1


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'contrato', 'usuario', 'monto', 'tipo_pago', 'estado', 'fecha']
    list_filter = ['estado', 'tipo_pago', 'fecha']
    search_fields = ['referencia', 'usuario__username']
    inlines = [DetallePagoInline]


@admin.register(DetallePago)
class DetallePagoAdmin(admin.ModelAdmin):
    list_display = ['pago', 'concepto', 'monto']
    search_fields = ['concepto']


@admin.register(HistorialPago)
class HistorialPagoAdmin(admin.ModelAdmin):
    list_display = ['pago', 'anterior', 'nuevo', 'usuario', 'fecha']
    list_filter = ['nuevo']


@admin.register(TipoPlan)
class TipoPlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_plan', 'precio', 'duracion', 'activo']
    list_filter = ['activo', 'tipo_plan']
    search_fields = ['nombre']


@admin.register(TransaccionStripe)
class TransaccionStripeAdmin(admin.ModelAdmin):
    list_display = ['id', 'contrato', 'pagador', 'propietario', 'monto', 'moneda', 'tipo_operacion', 'estado', 'creado']
    list_filter = ['estado', 'tipo_operacion', 'moneda']
    search_fields = ['stripe_session_id', 'stripe_payment_intent', 'descripcion']
    readonly_fields = ['stripe_session_id', 'stripe_payment_intent', 'comprobante_url']
