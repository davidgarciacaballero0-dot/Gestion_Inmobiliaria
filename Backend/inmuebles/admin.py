from django.contrib import admin
from .models import TipoInmueble, Inmueble, Publicacion, Multimedia, TipoContrato, Contrato, Comision, Direccion
from .models import Cita, HorarioDisponible

@admin.register(TipoInmueble)
class TipoInmuebleAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


class MultimediaInline(admin.TabularInline):
    model = Multimedia
    extra = 1


@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ['ciudad', 'zona', 'calle']
    search_fields = ['ciudad', 'zona', 'calle']


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'propietario', 'get_ciudad', 'get_precio_actual', 'estado', 'creado']
    list_filter = ['estado', 'tipo', 'direccion__ciudad']
    search_fields = ['titulo', 'direccion__calle', 'direccion__ciudad']
    inlines = [MultimediaInline]

    def get_ciudad(self, obj):
        return obj.direccion.ciudad if obj.direccion else 'N/A'
    get_ciudad.short_description = 'Ciudad'

    def get_precio_actual(self, obj):
        pub_activa = obj.publicaciones.filter(estado='activa').first()
        return f"{pub_activa.precio} USD ({pub_activa.get_tipo_oferta_display()})" if pub_activa else "Sin oferta activa"
    get_precio_actual.short_description = 'Precio/Oferta'


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'inmueble', 'tipo_oferta', 'precio', 'estado', 'creado']
    list_filter = ['estado', 'tipo_oferta']
    search_fields = ['inmueble__titulo']


@admin.register(Multimedia)
class MultimediaAdmin(admin.ModelAdmin):
    list_display = ['inmueble', 'tipo', 'principal', 'subido']
    list_filter = ['tipo', 'principal']


@admin.register(TipoContrato)
class TipoContratoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['id', 'inmueble', 'inquilino', 'tipo_contrato', 'monto', 'estado', 'inicio']
    list_filter = ['estado', 'tipo_contrato']
    search_fields = ['inmueble__titulo', 'inquilino__username']


@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'porcentaje', 'monto', 'pagada', 'fecha']
    list_filter = ['pagada']
@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display  = ['id', 'inmueble', 'cliente', 'propietario',
                     'fecha', 'hora_inicio', 'hora_fin', 'estado']
    list_filter   = ['estado', 'fecha']
    search_fields = ['inmueble__titulo', 'cliente__email', 'propietario__email']
    ordering      = ['-fecha', 'hora_inicio']


@admin.register(HorarioDisponible)
class HorarioDisponibleAdmin(admin.ModelAdmin):
    list_display  = ['propietario', 'inmueble', 'dia_semana',
                     'hora_inicio', 'hora_fin', 'activo']
    list_filter   = ['dia_semana', 'activo']
    search_fields = ['propietario__email']