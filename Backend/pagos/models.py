from django.db import models
from django.conf import settings
from inmuebles.models import Contrato


class TipoPago(models.Model):
    """Métodos de pago: efectivo, transferencia, QR, tarjeta, etc."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'pagos_tipo_pago'
        verbose_name = 'Tipo de Pago'
        verbose_name_plural = 'Tipos de Pago'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    """Registro de pago vinculado a un contrato."""

    class EstadoPago(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        COMPLETADO = 'completado', 'Completado'
        ANULADO = 'anulado', 'Anulado'
        PARCIAL = 'parcial', 'Parcial'

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name='pagos',
    )
    tipo_pago = models.ForeignKey(
        TipoPago,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pagos',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pagos',
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()
    referencia = models.CharField(max_length=100, blank=True)
    comprobante = models.FileField(upload_to='pagos/comprobantes/', blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE,
    )
    observaciones = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos_pago'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        # Primero guardamos en la base de datos local
        super().save(*args, **kwargs)
        
        # Sincronización asíncrona a Blockchain si fue completado
        if self.estado == 'completado':
            try:
                from inmuebles.blockchain_service import BlockchainService
                BlockchainService.registrar_pago(
                    pago_id=self.id,
                    contrato_id=self.contrato.id,
                    monto=self.monto,
                    fecha_str=self.fecha,
                    tipo_pago=self.tipo_pago.nombre if self.tipo_pago else "Efectivo",
                    transaction_id=self.referencia
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error sincronizando pago {self.id} con Blockchain: {str(e)}")

    def __str__(self):
        return f'Pago #{self.id} — {self.monto} Bs'


class DetallePago(models.Model):
    """Desglose o conceptos de un pago."""
    pago = models.ForeignKey(
        Pago,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    concepto = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'pagos_detalle_pago'
        verbose_name = 'Detalle de Pago'
        verbose_name_plural = 'Detalles de Pago'

    def __str__(self):
        return f'{self.concepto} — {self.monto} Bs'


class HistorialPago(models.Model):
    """Log de cambios de estado en un pago."""
    pago = models.ForeignKey(
        Pago,
        on_delete=models.CASCADE,
        related_name='historial',
    )
    anterior = models.CharField(max_length=20)
    nuevo = models.CharField(max_length=20)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historial_pagos',
    )

    class Meta:
        db_table = 'pagos_historial_pago'
        verbose_name = 'Historial de Pago'
        verbose_name_plural = 'Historial de Pagos'
        ordering = ['-fecha']

    def __str__(self):
        return f'Pago #{self.pago.id}: {self.anterior} → {self.nuevo}'


class TipoPlan(models.Model):
    """Categorías de planes de suscripción."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'pagos_tipo_plan'
        verbose_name = 'Tipo de Plan'
        verbose_name_plural = 'Tipos de Plan'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Plan(models.Model):
    """Plan de servicio/suscripción para el sistema."""
    tipo_plan = models.ForeignKey(
        TipoPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='planes',
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.PositiveIntegerField(default=1, help_text='Duración en meses')
    max_inmuebles = models.PositiveIntegerField(
        default=5,
        help_text='Cantidad máxima de inmuebles permitidos',
    )
    max_usuarios = models.PositiveIntegerField(
        default=1,
        help_text='Cantidad máxima de usuarios',
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos_plan'
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        ordering = ['precio']

    def __str__(self):
        return f'{self.nombre} — {self.precio} Bs/mes'


class TransaccionStripe(models.Model):
    """Registro de transacciones de pago procesadas por Stripe."""

    class EstadoTransaccion(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        COMPLETADA = 'completada', 'Completada'
        FALLIDA = 'fallida', 'Fallida'
        CANCELADA = 'cancelada', 'Cancelada'
        REEMBOLSADA = 'reembolsada', 'Reembolsada'

    class TipoOperacion(models.TextChoices):
        COMPRA = 'compra', 'Compra'
        ALQUILER = 'alquiler', 'Alquiler'
        DEPOSITO = 'deposito', 'Depósito'
        MENSUALIDAD = 'mensualidad', 'Mensualidad'

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name='transacciones_stripe',
    )
    pagador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transacciones_pagadas',
    )
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transacciones_recibidas',
    )
    tipo_operacion = models.CharField(
        max_length=20,
        choices=TipoOperacion.choices,
        default=TipoOperacion.MENSUALIDAD,
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=10, default='usd')
    descripcion = models.TextField(blank=True)
    stripe_session_id = models.CharField(max_length=255, unique=True, db_index=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.PENDIENTE,
    )
    comprobante_url = models.URLField(blank=True, help_text='URL del recibo de Stripe')
    chat = models.ForeignKey(
        'usuarios.Chat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pagos_transaccion_stripe'
        verbose_name = 'Transacción Stripe'
        verbose_name_plural = 'Transacciones Stripe'
        ordering = ['-creado']

    def __str__(self):
        return f'Tx #{self.id} — {self.monto} {self.moneda.upper()} ({self.estado})'


class ConfiguracionSistema(models.Model):
    """Configuración global del sistema. Implementa el patrón Singleton."""
    porcentaje_comision_plataforma = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text='Porcentaje de comisión por transacción (ej. 5.00 para 5%)'
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pagos_configuracion_sistema'
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'

    def save(self, *args, **kwargs):
        """Asegura que solo exista un registro de configuración."""
        if self.__class__.objects.count() > 0 and not self.pk:
            # Si ya existe un registro y se está intentando crear otro, se cancela
            return None
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Devuelve la instancia única o la crea si no existe."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Configuración Global del Sistema'
