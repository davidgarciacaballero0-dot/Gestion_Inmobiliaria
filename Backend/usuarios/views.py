from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Count

from .models import Usuario, Agenda, Notificacion, Chat, Mensaje, Bloqueo, Resena
from .services import crear_notificacion_sistema, crear_notificacion_usuario
from .serializers import (
    UsuarioSerializer,
    UsuarioCreateSerializer,
    AgendaSerializer,
    NotificacionSerializer,
    ChatSerializer,
    MensajeSerializer,
    BloqueoSerializer,
    ResenaSerializer,
)


class UsuarioViewSet(viewsets.ModelViewSet):
    """CRUD para usuarios."""
    queryset = Usuario.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me', permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Retorna o actualiza el perfil del usuario autenticado."""
        if request.method in ['PUT', 'PATCH']:
            serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='badges')
    def badges(self, request):
        """Contadores de cosas no leídas para el navbar."""
        user = request.user
        notif_count = Notificacion.objects.filter(usuario=user, leida=False).count()
        notif_sistema = Notificacion.objects.filter(
            usuario=user,
            leida=False,
            origen=Notificacion.OrigenNotificacion.SISTEMA,
        ).count()
        notif_usuario = Notificacion.objects.filter(
            usuario=user,
            leida=False,
            origen=Notificacion.OrigenNotificacion.USUARIO,
        ).count()
        
        # Mensajes no leídos en todos los chats del usuario
        chats = Chat.objects.filter(Q(participante1=user) | Q(participante2=user))
        msg_count = Mensaje.objects.filter(
            chat__in=chats,
            leido=False
        ).exclude(remitente=user).count()
        
        return Response({
            'notificaciones': notif_count,
            'notificaciones_sistema': notif_sistema,
            'notificaciones_usuario': notif_usuario,
            'mensajes': msg_count,
        })


class RegistroView(viewsets.GenericViewSet):
    """Endpoint público para registro de usuarios."""
    serializer_class = UsuarioCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UsuarioSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class AgendaViewSet(viewsets.ModelViewSet):
    """CRUD para eventos de agenda."""
    serializer_class = AgendaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if (user.is_staff or user.rol == 'admin') and self.request.query_params.get('personal') != 'true':
            return Agenda.objects.all()
        return Agenda.objects.filter(usuario=user)

    def perform_create(self, serializer):
        if 'usuario' not in serializer.validated_data:
            serializer.save(usuario=self.request.user)
        else:
            serializer.save()


class NotificacionViewSet(viewsets.ModelViewSet):
    """CRUD para notificaciones."""
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Notificacion.objects.all() if ((user.is_staff or user.rol == 'admin') and self.request.query_params.get('personal') != 'true') else Notificacion.objects.filter(usuario=user)
        
        # Filtrar por origen si se especifica
        origen = self.request.query_params.get('origen')
        if origen in ['sistema', 'usuario']:
            qs = qs.filter(origen=origen)
        return qs

    def perform_create(self, serializer):
        if 'usuario' not in serializer.validated_data:
            serializer.save(
                usuario=self.request.user,
                origen=Notificacion.OrigenNotificacion.USUARIO,
            )
        else:
            serializer.save(origen=Notificacion.OrigenNotificacion.SISTEMA)

    @action(detail=False, methods=['get'], url_path='sistema')
    def sistema(self, request):
        qs = self.get_queryset().filter(origen=Notificacion.OrigenNotificacion.SISTEMA)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='usuario')
    def usuario(self, request):
        qs = self.get_queryset().filter(origen=Notificacion.OrigenNotificacion.USUARIO)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='usuario-confirmacion')
    def usuario_confirmacion(self, request):
        titulo = (request.data.get('titulo') or '').strip()
        mensaje = (request.data.get('mensaje') or '').strip()
        if not titulo or not mensaje:
            return Response({'error': 'titulo y mensaje son requeridos'}, status=400)

        notif = crear_notificacion_usuario(
            usuario=request.user,
            titulo=titulo,
            mensaje=mensaje,
            tipo=Notificacion.TipoNotificacion.CONFIRMACION,
        )
        serializer = self.get_serializer(notif)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='sistema-alerta')
    def sistema_alerta(self, request):
        if not (request.user.is_staff or request.user.rol == 'admin'):
            return Response({'error': 'No autorizado'}, status=403)

        usuario_id = request.data.get('usuario')
        titulo = (request.data.get('titulo') or '').strip()
        mensaje = (request.data.get('mensaje') or '').strip()
        tipo = request.data.get('tipo') or Notificacion.TipoNotificacion.ALERTA
        if not usuario_id or not titulo or not mensaje:
            return Response({'error': 'usuario, titulo y mensaje son requeridos'}, status=400)

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=404)

        notif = crear_notificacion_sistema(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
        )
        serializer = self.get_serializer(notif)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='marcar-leidas')
    def marcar_leidas(self, request):
        """Marca todas las notificaciones como leídas."""
        origen = request.data.get('origen')
        qs = self.get_queryset().filter(leida=False)
        if origen in ['sistema', 'usuario']:
            qs = qs.filter(origen=origen)
        qs.update(leida=True)
        return Response({'status': 'Notificaciones marcadas como leídas'})


class ChatViewSet(viewsets.ModelViewSet):
    """CRUD para Chats."""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        qs = Chat.objects.filter(Q(participante1=user) | Q(participante2=user)).distinct()
        return qs

    def create(self, request, *args, **kwargs):
        part1 = request.data.get('participante1') or request.user.id
        part2 = request.data.get('participante2')
        inm = request.data.get('inmueble')

        if not part2:
            return Response({'error': 'participante2 es requerido'}, status=400)

        # Verificar bloqueos
        if Bloqueo.objects.filter(
            Q(bloqueador_id=part1, bloqueado_id=part2) | 
            Q(bloqueador_id=part2, bloqueado_id=part1)
        ).exists():
            return Response({'error': 'No puedes chatear con este usuario'}, status=403)

        # Buscar chat existente en cualquier dirección
        chat = Chat.objects.filter(
            (Q(participante1_id=part1) & Q(participante2_id=part2)) |
            (Q(participante1_id=part2) & Q(participante2_id=part1))
        ).first()

        if chat:
            serializer = self.get_serializer(chat)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Crear nuevo chat
        chat = Chat.objects.create(
            participante1_id=part1,
            participante2_id=part2,
            inmueble_id=inm
        )
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='mensajes')
    def listar_mensajes(self, request, pk=None):
        chat = self.get_object()
        mensajes = chat.mensajes.all().order_by('creado')
        # Marcar como leídos los que no son míos
        mensajes.exclude(remitente=request.user).filter(leido=False).update(leido=True)
        serializer = MensajeSerializer(mensajes, many=True)
        return Response(serializer.data)


class MensajeViewSet(viewsets.ModelViewSet):
    """CRUD para Mensajes con soporte de archivos."""
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        return Mensaje.objects.filter(Q(chat__participante1=user) | Q(chat__participante2=user)).distinct()

    def create(self, request, *args, **kwargs):
        tipo = request.data.get('tipo') or request.data.get('tipo_mensaje') or 'texto'
        chat_id = request.data.get('chat')
        contenido = request.data.get('contenido', '')
        archivo_file = request.FILES.get('archivo')
        ubicacion_val = request.data.get('ubicacion') or request.data.get('ubicacion_gps') or ''
        
        # Verificar bloqueos
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat no encontrado'}, status=404)
        
        other_user = chat.participante2 if chat.participante1 == request.user else chat.participante1
        if Bloqueo.objects.filter(
            Q(bloqueador=request.user, bloqueado=other_user) |
            Q(bloqueador=other_user, bloqueado=request.user)
        ).exists():
            return Response({'error': 'Bloqueado: no puedes enviar mensajes'}, status=403)

        archivo_url = ''
        if archivo_file and tipo in ['imagen', 'video']:
            import cloudinary
            import cloudinary.uploader
            from django.conf import settings
            
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
                api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
                api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
            )
            upload_data = cloudinary.uploader.upload(
                archivo_file,
                resource_type='auto' if tipo == 'video' else 'image'
            )
            archivo_url = upload_data.get('secure_url', '')

        if tipo == 'whatsapp' and not contenido:
            return Response({'error': 'Debes enviar un número de WhatsApp válido'}, status=400)

        if tipo == 'recorrido360':
            if not chat.inmueble:
                return Response({'error': 'Este chat no está asociado a ningún inmueble.'}, status=400)
            if chat.inmueble.propietario != request.user and not request.user.is_staff:
                return Response({'error': 'Solo el propietario de este inmueble puede otorgar acceso al recorrido 360°.'}, status=403)

        msg = Mensaje.objects.create(

            chat_id=chat_id,
            remitente=request.user,
            tipo=tipo,
            contenido=contenido,
            archivo=archivo_url,
            ubicacion=ubicacion_val,
        )
        
        # Actualizar timestamp del chat
        chat.save()  # triggers auto_now on actualizado

        receptor = chat.participante2 if chat.participante1 == request.user else chat.participante1
        if receptor != request.user:
            crear_notificacion_usuario(
                usuario=receptor,
                titulo='Nuevo mensaje recibido',
                mensaje=f'Tienes un nuevo mensaje de {request.user.get_full_name() or request.user.email}.',
                tipo=Notificacion.TipoNotificacion.CONFIRMACION,
            )

        serializer = MensajeSerializer(msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BloqueoViewSet(viewsets.ModelViewSet):
    """Gestión de bloqueos entre usuarios."""
    serializer_class = BloqueoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bloqueo.objects.filter(bloqueador=self.request.user)

    def perform_create(self, serializer):
        serializer.save(bloqueador=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        """Bloquear/Desbloquear un usuario."""
        bloqueado_id = request.data.get('bloqueado')
        if not bloqueado_id:
            return Response({'error': 'Falta el ID del usuario'}, status=400)
        
        bloqueo = Bloqueo.objects.filter(bloqueador=request.user, bloqueado_id=bloqueado_id).first()
        if bloqueo:
            bloqueo.delete()
            return Response({'bloqueado': False, 'status': 'Usuario desbloqueado'})
        
        Bloqueo.objects.create(bloqueador=request.user, bloqueado_id=bloqueado_id)
        return Response({'bloqueado': True, 'status': 'Usuario bloqueado'})
    
    @action(detail=False, methods=['get'], url_path='check/(?P<user_id>[^/.]+)')
    def check(self, request, user_id=None):
        """Verificar si un usuario está bloqueado."""
        is_blocked = Bloqueo.objects.filter(bloqueador=request.user, bloqueado_id=user_id).exists()
        blocked_me = Bloqueo.objects.filter(bloqueador_id=user_id, bloqueado=request.user).exists()
        return Response({'bloqueado_por_mi': is_blocked, 'me_bloqueo': blocked_me})


class ResenaViewSet(viewsets.ModelViewSet):
    """CRUD para reseñas de inmuebles."""
    serializer_class = ResenaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        inmueble_id = self.request.query_params.get('inmueble')
        qs = Resena.objects.select_related('usuario', 'inmueble')
        if inmueble_id:
            qs = qs.filter(inmueble_id=inmueble_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=['get'], url_path='promedio/(?P<inmueble_id>[^/.]+)')
    def promedio(self, request, inmueble_id=None):
        """Obtener promedio de calificación de un inmueble."""
        from django.db.models import Avg
        result = Resena.objects.filter(inmueble_id=inmueble_id).aggregate(
            promedio=Avg('calificacion'),
            total=Count('id')
        )
        return Response({
            'promedio': round(result['promedio'] or 0, 1),
            'total': result['total']
        })


from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para retornar tokens y datos del usuario.
    """
    serializer_class = CustomTokenObtainPairSerializer
