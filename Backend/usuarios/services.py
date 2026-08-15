from .models import Notificacion


def crear_notificacion_sistema(*, usuario, titulo, mensaje, tipo=Notificacion.TipoNotificacion.INFO):
    return Notificacion.objects.create(
        usuario=usuario,
        origen=Notificacion.OrigenNotificacion.SISTEMA,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )


def crear_notificacion_usuario(*, usuario, titulo, mensaje, tipo=Notificacion.TipoNotificacion.CONFIRMACION):
    return Notificacion.objects.create(
        usuario=usuario,
        origen=Notificacion.OrigenNotificacion.USUARIO,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )
