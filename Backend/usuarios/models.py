from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    username = None 
    email = models.EmailField(unique=True) 

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 

    class RolesConfig(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        USUARIO = 'usuario', 'Usuario'

    rol = models.CharField(
        max_length=20,
        choices=RolesConfig.choices,
        default=RolesConfig.USUARIO,
    )
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)
    nacimiento = models.DateField(null=True, blank=True)
    ci = models.CharField('Cédula de Identidad', max_length=20, blank=True, db_index=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'usuarios_usuario'
        ordering = ['-id']

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'


class Agenda(models.Model):
    """Eventos y citas del usuario."""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='agendas',
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    inicio = models.DateTimeField()
    fin = models.DateTimeField(null=True, blank=True)
    ubicacion = models.CharField(max_length=255, blank=True)
    completado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios_agenda'
        verbose_name = 'Agenda'
        verbose_name_plural = 'Agendas'
        ordering = ['-inicio']

    def __str__(self):
        return f'{self.titulo} — {self.usuario.email}'


class Notificacion(models.Model):
    """Notificaciones del sistema para el usuario."""

    class TipoNotificacion(models.TextChoices):
        INFO = 'info', 'Información'
        ALERTA = 'alerta', 'Alerta'
        RECORDATORIO = 'recordatorio', 'Recordatorio'
        PAGO = 'pago', 'Pago'
        CONFIRMACION = 'confirmacion', 'Confirmación'

    class OrigenNotificacion(models.TextChoices):
        SISTEMA = 'sistema', 'Sistema'
        USUARIO = 'usuario', 'Usuario'

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoNotificacion.choices,
        default=TipoNotificacion.INFO,
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenNotificacion.choices,
        default=OrigenNotificacion.SISTEMA,
    )
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios_notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-creada']

    def __str__(self):
        return f'{self.titulo} → {self.usuario.email}'


class Bloqueo(models.Model):
    """Un usuario bloquea a otro."""
    bloqueador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='bloqueos_hechos')
    bloqueado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='bloqueos_recibidos')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios_bloqueo'
        unique_together = ('bloqueador', 'bloqueado')
        verbose_name = 'Bloqueo'
        verbose_name_plural = 'Bloqueos'

    def __str__(self):
        return f'{self.bloqueador.email} bloqueó a {self.bloqueado.email}'


class Chat(models.Model):
    """Conversaciones entre usuarios."""
    participante1 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='chats_iniciados')
    participante2 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='chats_recibidos')
    inmueble = models.ForeignKey('inmuebles.Inmueble', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    publicacion = models.ForeignKey('inmuebles.Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuarios_conversacion'
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
        ordering = ['-actualizado']

    def __str__(self):
        desc = f"Chat: {self.participante1.email} - {self.participante2.email}"
        if self.inmueble:
            desc += f" (Inm: {self.inmueble.id})"
        if self.publicacion:
            desc += f" (Pub: {self.publicacion.id})"
        return desc


class Mensaje(models.Model):
    """Mensaje individual en un chat."""

    class TipoMensaje(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        IMAGEN = 'imagen', 'Imagen'
        VIDEO = 'video', 'Video'
        UBICACION = 'ubicacion', 'Ubicación'
        EMOJI = 'emoji', 'Emoji'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        RECORRIDO_360 = 'recorrido360', 'Recorrido 360°'


    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensajes')
    remitente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mensajes_enviados')
    tipo = models.CharField(
        max_length=20,
        choices=TipoMensaje.choices,
        default=TipoMensaje.TEXTO,
    )
    contenido = models.TextField(blank=True)
    archivo = models.CharField(max_length=500, blank=True, help_text='URL de imagen/video en Cloudinary')
    ubicacion = models.CharField(max_length=100, blank=True, help_text='lat, lng para mensajes de ubicación')
    leido = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios_mensaje'
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['creado']

    def __str__(self):
        return f'Msg de {self.remitente.email} - {self.creado.strftime("%Y-%m-%d %H:%M")}'


class Resena(models.Model):
    """Reseña/opinión de un usuario sobre un inmueble."""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas')
    inmueble = models.ForeignKey('inmuebles.Inmueble', on_delete=models.CASCADE, related_name='resenas')
    calificacion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Calificación de 1 a 5 estrellas'
    )
    comentario = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuarios_resena'
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        unique_together = ('usuario', 'inmueble')
        ordering = ['-creado']

    def __str__(self):
        return f'{self.usuario.email} → {self.inmueble.titulo} ({self.calificacion}★)'

from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
import channels.layers

@receiver(post_save, sender=Mensaje)
def notificar_nuevo_mensaje(sender, instance, created, **kwargs):
    if created:
        channel_layer = channels.layers.get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'chat_{instance.chat.id}',
                {
                    'type': 'chat_message',
                    'action': 'new_message',
                    'chat_id': instance.chat.id,
                    'mensaje_id': instance.id,
                }
            )
            event = {
                'type': 'user_event',
                'action': 'new_message',
                'chat_id': instance.chat.id,
                'mensaje_id': instance.id,
            }
            async_to_sync(channel_layer.group_send)(f'user_{instance.chat.participante1.id}', event)
            async_to_sync(channel_layer.group_send)(f'user_{instance.chat.participante2.id}', event)
