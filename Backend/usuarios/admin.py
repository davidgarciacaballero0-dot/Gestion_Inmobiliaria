from django.contrib import admin
from .models import Usuario, Agenda, Notificacion




@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'rol', 'activo']
    list_filter = ['rol', 'activo', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'ci']


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'inicio', 'completado']
    list_filter = ['completado', 'inicio']
    search_fields = ['titulo', 'usuario__username']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'tipo', 'origen', 'leida', 'creada']
    list_filter = ['tipo', 'origen', 'leida']
    search_fields = ['titulo', 'usuario__username']
