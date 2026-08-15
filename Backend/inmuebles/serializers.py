from rest_framework import serializers
from .models import TipoInmueble, Inmueble, Publicacion, Multimedia, TipoContrato, Contrato, Comision, Favorito, Direccion, Hotspot, VerificacionTitulo


class TipoInmuebleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoInmueble
        fields = '__all__'


class HotspotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotspot
        fields = ['id', 'inmueble', 'escena_origen', 'escena_destino', 'pitch', 'yaw', 'texto_ayuda']


class MultimediaSerializer(serializers.ModelSerializer):
    hotspots = HotspotSerializer(many=True, source='hotspots_salida', read_only=True)

    class Meta:
        model = Multimedia
        fields = ['id', 'inmueble', 'tipo', 'archivo', 'descripcion', 'principal', 'orden', 'subido', 'hotspots']
        read_only_fields = ['id', 'subido']


class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = '__all__'


class PublicacionSerializer(serializers.ModelSerializer):
    tipo_oferta_display = serializers.CharField(source='get_tipo_oferta_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    inmueble_titulo = serializers.CharField(source='inmueble.titulo', read_only=True)

    class Meta:
        model = Publicacion
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'actualizado']


class InmuebleSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    propietario_nombre = serializers.CharField(
        source='propietario.get_full_name', read_only=True
    )
    multimedia = MultimediaSerializer(many=True, read_only=True)
    direccion = DireccionSerializer()
    precio = serializers.SerializerMethodField(read_only=True)
    tipo_oferta = serializers.SerializerMethodField(read_only=True)
    publicaciones = PublicacionSerializer(many=True, read_only=True)
    verificacion_estado = serializers.SerializerMethodField(read_only=True)
    verificacion_score = serializers.SerializerMethodField(read_only=True)
    verificacion_resumen = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Inmueble
        fields = '__all__'
        read_only_fields = ['id', 'propietario', 'creado', 'actualizado', 'superficie']

    def get_precio(self, obj):
        pub_activa = obj.publicaciones.filter(estado='activa').first()
        return pub_activa.precio if pub_activa else None

    def get_tipo_oferta(self, obj):
        pub_activa = obj.publicaciones.filter(estado='activa').first()
        return pub_activa.tipo_oferta if pub_activa else None

    def create(self, validated_data):
        direccion_data = validated_data.pop('direccion', None)
        direccion = Direccion.objects.create(**direccion_data) if direccion_data else None
        return Inmueble.objects.create(direccion=direccion, **validated_data)

    def update(self, instance, validated_data):
        direccion_data = validated_data.pop('direccion', None)
        if direccion_data:
            if instance.direccion:
                for attr, value in direccion_data.items():
                    setattr(instance.direccion, attr, value)
                instance.direccion.save()
            else:
                direccion = Direccion.objects.create(**direccion_data)
                instance.direccion = direccion
        return super().update(instance, validated_data)

    def get_verificacion_estado(self, obj):
        try:
            return obj.verificacion_titulo.estado
        except Exception:
            return None

    def get_verificacion_score(self, obj):
        try:
            return obj.verificacion_titulo.score_confianza
        except Exception:
            return None

    def get_verificacion_resumen(self, obj):
        try:
            return obj.verificacion_titulo.resumen_publico
        except Exception:
            return None



class InmuebleListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados."""
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    is_favorito = serializers.SerializerMethodField()
    imagen_principal = serializers.SerializerMethodField()
    direccion = DireccionSerializer(read_only=True)
    precio = serializers.SerializerMethodField(read_only=True)
    tipo_oferta = serializers.SerializerMethodField(read_only=True)
    verificacion_estado = serializers.SerializerMethodField(read_only=True)
    verificacion_score = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Inmueble
        fields = [
            'id', 'titulo', 'tipo_nombre', 'direccion',
            'precio', 'tipo_oferta', 'estado', 'habitaciones', 'banos',
            'imagen_principal', 'creado', 'is_favorito',
            'largo', 'ancho', 'superficie',
            'verificacion_estado', 'verificacion_score'
        ]

    def get_precio(self, obj):
        pub_activa = obj.publicaciones.filter(estado='activa').first()
        return pub_activa.precio if pub_activa else None

    def get_tipo_oferta(self, obj):
        pub_activa = obj.publicaciones.filter(estado='activa').first()
        return pub_activa.tipo_oferta if pub_activa else None

    def get_is_favorito(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Verificación directa por ID para evitar problemas de LazyObjects
        return Favorito.objects.filter(usuario_id=request.user.id, inmueble_id=obj.id).exists()

    def get_imagen_principal(self, obj):
        try:
            img = obj.multimedia.filter(principal=True).first()
            if not img:
                img = obj.multimedia.first()
            
            if img and img.archivo:
                return img.archivo
        except Exception:
            pass
        return None

    def get_verificacion_estado(self, obj):
        try:
            return obj.verificacion_titulo.estado
        except Exception:
            return None

    def get_verificacion_score(self, obj):
        try:
            return obj.verificacion_titulo.score_confianza
        except Exception:
            return None


class VerificacionTituloSerializer(serializers.ModelSerializer):
    solicitado_por_nombre = serializers.CharField(source='solicitado_por.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = VerificacionTitulo
        fields = '__all__'
        read_only_fields = ['id', 'solicitado_por', 'texto_ocr', 'resultado_ia', 'estado', 'score_confianza', 'resumen_publico', 'creado', 'actualizado']



class TipoContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoContrato
        fields = '__all__'


class ContratoSerializer(serializers.ModelSerializer):
    inmueble_titulo = serializers.CharField(source='inmueble.titulo', read_only=True)
    inmueble_direccion = serializers.SerializerMethodField(read_only=True)
    propietario_nombre = serializers.SerializerMethodField(read_only=True)
    propietario_ci = serializers.SerializerMethodField(read_only=True)
    propietario_telefono = serializers.SerializerMethodField(read_only=True)
    propietario_email = serializers.SerializerMethodField(read_only=True)
    inquilino_nombre = serializers.CharField(
        source='inquilino.get_full_name', read_only=True
    )
    inquilino_ci = serializers.CharField(source='inquilino.ci', read_only=True)
    inquilino_telefono = serializers.CharField(source='inquilino.telefono', read_only=True)
    inquilino_email = serializers.CharField(source='inquilino.email', read_only=True)
    tipo_contrato_nombre = serializers.CharField(
        source='tipo_contrato.nombre', read_only=True
    )

    class Meta:
        model = Contrato
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'actualizado']

    def get_inmueble_direccion(self, obj):
        if obj.inmueble and obj.inmueble.direccion:
            d = obj.inmueble.direccion
            return f'{d.ciudad}, {d.zona} - {d.calle}'
        return ''

    def get_propietario_nombre(self, obj):
        return obj.inmueble.propietario.get_full_name() if obj.inmueble else ''

    def get_propietario_ci(self, obj):
        return obj.inmueble.propietario.ci if obj.inmueble else ''

    def get_propietario_telefono(self, obj):
        return obj.inmueble.propietario.telefono if obj.inmueble else ''

    def get_propietario_email(self, obj):
        return obj.inmueble.propietario.email if obj.inmueble else ''


class ComisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comision
        fields = '__all__'
        read_only_fields = ['id', 'fecha']


class FavoritoSerializer(serializers.ModelSerializer):
    inmueble_data = InmuebleListSerializer(source='inmueble', read_only=True)

    class Meta:
        model = Favorito
        fields = ['id', 'inmueble', 'inmueble_data', 'creado']
        read_only_fields = ['id', 'creado']

from .models import Cita, HorarioDisponible


class HorarioDisponibleSerializer(serializers.ModelSerializer):
    dia_nombre = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model  = HorarioDisponible
        fields = '__all__'
        read_only_fields = ['id', 'propietario']


class CitaSerializer(serializers.ModelSerializer):
    cliente_nombre    = serializers.CharField(source='cliente.get_full_name',    read_only=True)
    propietario_nombre = serializers.CharField(source='propietario.get_full_name', read_only=True)
    inmueble_titulo   = serializers.CharField(source='inmueble.titulo',          read_only=True)

    class Meta:
        model  = Cita
        fields = '__all__'
        read_only_fields = ['id', 'cliente', 'propietario', 'hora_fin', 'creado', 'actualizado']

    def validate(self, data):
        inmueble    = data.get('inmueble')
        fecha       = data.get('fecha')
        hora_inicio = data.get('hora_inicio')

        if inmueble and fecha and hora_inicio:
            qs = Cita.objects.filter(
                inmueble=inmueble,
                fecha=fecha,
                hora_inicio=hora_inicio,
                estado__in=['pendiente', 'confirmada'],
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'hora_inicio': 'Ya existe una cita agendada para ese horario.'}
                )
        return data


from .models import AccesoRecorrido360

class AccesoRecorrido360Serializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.get_full_name', read_only=True)
    propietario_nombre = serializers.CharField(source='propietario.get_full_name', read_only=True)
    inmueble_titulo = serializers.CharField(source='inmueble.titulo', read_only=True)
    es_valido = serializers.BooleanField(read_only=True)

    class Meta:
        model = AccesoRecorrido360
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'propietario', 'visitas', 'ultimo_acceso_visor']

