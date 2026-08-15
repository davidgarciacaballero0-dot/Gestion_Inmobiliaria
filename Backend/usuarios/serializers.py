from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, Agenda, Notificacion, Chat, Mensaje, Bloqueo, Resena


class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'rol', 'rol_nombre', 'telefono', 'direccion', 'foto',
            'nacimiento', 'ci', 'activo', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios con contraseña."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'password', 'first_name',
            'last_name', 'rol', 'telefono', 'direccion',
            'nacimiento', 'ci',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AgendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agenda
        fields = '__all__'
        read_only_fields = ['id', 'creado']
        extra_kwargs = {'usuario': {'required': False}}


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ['id', 'creada']
        extra_kwargs = {'usuario': {'required': False}}


class MensajeSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.SerializerMethodField(read_only=True)
    tipo_mensaje = serializers.CharField(source='tipo', read_only=True)
    archivo_url = serializers.CharField(source='archivo', read_only=True)
    ubicacion_gps = serializers.CharField(source='ubicacion', read_only=True)

    class Meta:
        model = Mensaje
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'remitente']

    def get_remitente_nombre(self, obj):
        return f'{obj.remitente.first_name} {obj.remitente.last_name}'


class ChatSerializer(serializers.ModelSerializer):
    participante1_nombre = serializers.CharField(source='participante1.get_full_name', read_only=True)
    participante2_nombre = serializers.CharField(source='participante2.get_full_name', read_only=True)
    participante1_email = serializers.CharField(source='participante1.email', read_only=True)
    participante2_email = serializers.CharField(source='participante2.email', read_only=True)
    inmueble_titulo = serializers.SerializerMethodField(read_only=True)
    ultimo_mensaje = serializers.SerializerMethodField(read_only=True)
    no_leidos = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chat
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'actualizado']

    def get_inmueble_titulo(self, obj):
        return obj.inmueble.titulo if obj.inmueble else None

    def get_ultimo_mensaje(self, obj):
        msg = obj.mensajes.order_by('-creado').first()
        if msg:
            return MensajeSerializer(msg).data
        return None

    def get_no_leidos(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.mensajes.exclude(remitente=request.user).filter(leido=False).count()
        return 0


class BloqueoSerializer(serializers.ModelSerializer):
    bloqueado_nombre = serializers.CharField(source='bloqueado.get_full_name', read_only=True)
    bloqueado_email = serializers.CharField(source='bloqueado.email', read_only=True)

    class Meta:
        model = Bloqueo
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'bloqueador']


class ResenaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = Resena
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'actualizado', 'usuario']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['usuario'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'rol': self.user.rol,
            'foto': self.user.foto.url if self.user.foto else None
        }
        
        return data
