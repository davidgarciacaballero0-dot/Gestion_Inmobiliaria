from rest_framework import serializers
from .models import TipoPago, Pago, DetallePago, HistorialPago, TipoPlan, Plan, TransaccionStripe, ConfiguracionSistema


class TipoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPago
        fields = '__all__'


class DetallePagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePago
        fields = '__all__'
        read_only_fields = ['id']


class PagoSerializer(serializers.ModelSerializer):
    tipo_pago_nombre = serializers.CharField(source='tipo_pago.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    detalles = DetallePagoSerializer(many=True, read_only=True)
    inmueble_titulo = serializers.CharField(source='contrato.inmueble.titulo', read_only=True)
    inmueble_id = serializers.IntegerField(source='contrato.inmueble.id', read_only=True)

    class Meta:
        model = Pago
        fields = [
            'id', 'contrato', 'tipo_pago', 'tipo_pago_nombre', 'usuario', 'usuario_nombre',
            'monto', 'fecha', 'referencia', 'estado', 'observaciones', 'creado',
            'detalles', 'inmueble_titulo', 'inmueble_id'
        ]
        read_only_fields = ['id', 'creado']


class HistorialPagoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = HistorialPago
        fields = '__all__'
        read_only_fields = ['id', 'fecha']


class TipoPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPlan
        fields = '__all__'


class PlanSerializer(serializers.ModelSerializer):
    tipo_plan_nombre = serializers.CharField(source='tipo_plan.nombre', read_only=True)

    class Meta:
        model = Plan
        fields = '__all__'
        read_only_fields = ['id', 'creado']


class TransaccionStripeSerializer(serializers.ModelSerializer):
    pagador_nombre = serializers.CharField(source='pagador.get_full_name', read_only=True)
    propietario_nombre = serializers.CharField(source='propietario.get_full_name', read_only=True)
    inmueble_titulo = serializers.SerializerMethodField(read_only=True)
    contrato_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TransaccionStripe
        fields = '__all__'
        read_only_fields = ['id', 'creado', 'actualizado']

    def get_inmueble_titulo(self, obj):
        return obj.contrato.inmueble.titulo if obj.contrato and obj.contrato.inmueble else None

    def get_contrato_info(self, obj):
        if obj.contrato:
            return f'Contrato #{obj.contrato.id} — {obj.contrato.inmueble.titulo}'
        return None

class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionSistema
        fields = '__all__'
