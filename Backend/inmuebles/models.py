from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class TipoInmueble(models.Model):
    """Categorías de inmuebles: casa, departamento, terreno, oficina, etc."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'inmuebles_tipo_inmueble'
        verbose_name = 'Tipo de Inmueble'
        verbose_name_plural = 'Tipos de Inmueble'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Direccion(models.Model):
    """Normalización de datos de ubicación geográfica."""
    ciudad = models.CharField(max_length=100)
    zona = models.CharField(max_length=100, blank=True)
    calle = models.CharField(max_length=200, blank=True)
    referencia = models.TextField(blank=True)

    class Meta:
        db_table = 'inmuebles_direccion'
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'

    def __str__(self):
        return f'{self.ciudad}, {self.zona} - {self.calle}'


class Inmueble(models.Model):
    """Propiedad inmobiliaria."""

    class EstadoInmueble(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        OCUPADO = 'ocupado', 'Ocupado'
        EN_MANTENIMIENTO = 'mantenimiento', 'En Mantenimiento'
        RESERVADO = 'reservado', 'Reservado'
        OCULTO = 'oculto', 'Oculto'

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inmuebles',
    )
    tipo = models.ForeignKey(
        TipoInmueble,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inmuebles',
    )
    direccion = models.OneToOneField(
        'Direccion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inmueble'
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    largo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ancho = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    superficie = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Superficie en metros cuadrados',
        null=True, blank=True,
        db_index=True
    )
    valor_activo = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        help_text='Valor catastral o de referencia del activo físico (DDRR). Interno, no se publica.'
    )
    habitaciones = models.PositiveIntegerField(default=0, db_index=True)
    banos = models.PositiveIntegerField(default=0, db_index=True)
    garaje = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=20,
        choices=EstadoInmueble.choices,
        default=EstadoInmueble.DISPONIBLE,
        db_index=True
    )
    # Coordenadas GPS
    gps = models.CharField(max_length=100, null=True, blank=True, help_text="Coordenadas GPS (ej. -17.7898, -63.1939)")
    modelo_3d = models.CharField(max_length=500, null=True, blank=True, help_text="URL del modelo 3D (.glb) para visualización AR")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inmuebles_inmueble'
        verbose_name = 'Inmueble'
        verbose_name_plural = 'Inmuebles'
        ordering = ['-creado']

    def save(self, *args, **kwargs):
        if self.largo is not None and self.ancho is not None:
            self.superficie = self.largo * self.ancho
        super().save(*args, **kwargs)

    def __str__(self):
        ciudad_str = self.direccion.ciudad if self.direccion else 'Sin ciudad'
        return f'{self.titulo} — {ciudad_str}'


class Multimedia(models.Model):
    """Imágenes y videos de un inmueble."""

    class TipoArchivo(models.TextChoices):
        IMAGEN = 'imagen', 'Imagen'
        VIDEO = 'video', 'Video'
        PANORAMA360 = 'panorama360', 'Panorama 360°'
        MUSICA = 'musica', 'Música'

    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='multimedia',
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoArchivo.choices,
        default=TipoArchivo.IMAGEN,
    )
    archivo = models.CharField(max_length=500, help_text='URL de Cloudinary o ruta')
    descripcion = models.CharField(max_length=200, blank=True)
    principal = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de visualización")
    subido = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inmuebles_multimedia'
        verbose_name = 'Multimedia'
        verbose_name_plural = 'Multimedia'
        ordering = ['orden', '-principal', '-subido']

    def __str__(self):
        return f'{self.tipo} — {self.inmueble.titulo}'


class Hotspot(models.Model):
    """
    Define un punto de transición espacial interactivo (hotspot)
    desde un panorama de origen hacia otro panorama de destino.
    """
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='hotspots',
        help_text="Inmueble al que pertenece el recorrido"
    )
    escena_origen = models.ForeignKey(
        Multimedia,
        on_delete=models.CASCADE,
        related_name='hotspots_salida',
        help_text="Panorama de origen donde se dibuja el hotspot (debe ser tipo panorama360)"
    )
    escena_destino = models.ForeignKey(
        Multimedia,
        on_delete=models.CASCADE,
        related_name='hotspots_entrada',
        help_text="Panorama destino al cual viajará el visor al hacer clic"
    )

    # Coordenadas esféricas de Pannellum
    pitch = models.FloatField(
        help_text="Ángulo vertical (-90 a 90 grados)"
    )
    yaw = models.FloatField(
        help_text="Ángulo horizontal (-180 a 180 grados)"
    )

    # Metadatos del hotspot
    texto_ayuda = models.CharField(
        max_length=100,
        blank=True,
        help_text="Texto informativo que aparece al pasar el cursor (tooltip), ej: 'Ir a Cocina'"
    )

    class Meta:
        db_table = 'inmuebles_hotspot'
        verbose_name = 'Punto de Transición (Hotspot)'
        verbose_name_plural = 'Puntos de Transición (Hotspots)'
        unique_together = ('escena_origen', 'escena_destino')

    def clean(self):
        # Regla de Integridad de Dominio (SOLID / Validación Temprana)
        if self.escena_origen.tipo != Multimedia.TipoArchivo.PANORAMA360:
            raise ValidationError("La escena de origen debe ser un panorama 360°.")
        if self.escena_destino.tipo != Multimedia.TipoArchivo.PANORAMA360:
            raise ValidationError("La escena de destino debe ser un panorama 360°.")
        if self.escena_origen.inmueble != self.inmueble or self.escena_destino.inmueble != self.inmueble:
            raise ValidationError("Ambos panoramas deben pertenecer al mismo inmueble.")
        if self.escena_origen == self.escena_destino:
            raise ValidationError("No se puede crear un hotspot que apunte a la misma escena de origen.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Hotspot: {self.escena_origen.descripcion} -> {self.escena_destino.descripcion}"


class Publicacion(models.Model):
    """Oferta comercial de un inmueble en el catálogo."""

    class TipoOferta(models.TextChoices):
        ALQUILER = 'alquiler', 'Alquiler'
        VENTA = 'venta', 'Venta'
        ANTICRETICO = 'anticretico', 'Anticrético'

    class EstadoPublicacion(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        ACTIVA = 'activa', 'Activa'
        PAUSADA = 'pausada', 'Pausada'
        FINALIZADA = 'finalizada', 'Finalizada'

    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='publicaciones',
    )
    tipo_oferta = models.CharField(
        max_length=20,
        choices=TipoOferta.choices,
        default=TipoOferta.ALQUILER,
        db_index=True
    )
    precio = models.DecimalField(
        max_digits=12, decimal_places=2, db_index=True,
        validators=[MinValueValidator(0)]
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoPublicacion.choices,
        default=EstadoPublicacion.BORRADOR,
        db_index=True
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inmuebles_publicacion'
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-creado']

    def save(self, *args, **kwargs):
        # Si esta publicación se activa, debemos desactivar cualquier otra activa para este inmueble
        if self.estado == self.EstadoPublicacion.ACTIVA:
            Publicacion.objects.filter(
                inmueble=self.inmueble,
                estado=self.EstadoPublicacion.ACTIVA
            ).exclude(pk=self.pk).update(estado=self.EstadoPublicacion.FINALIZADA)
            
            # Opcionalmente, actualizamos el estado del inmueble físico a disponible
            if self.inmueble.estado != Inmueble.EstadoInmueble.DISPONIBLE:
                self.inmueble.estado = Inmueble.EstadoInmueble.DISPONIBLE
                self.inmueble.save(update_fields=['estado'])
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_tipo_oferta_display()} — {self.inmueble.titulo} ({self.precio} USD)'


class TipoContrato(models.Model):
    """Tipos de contrato: alquiler, venta, anticrético, etc."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'inmuebles_tipo_contrato'
        verbose_name = 'Tipo de Contrato'
        verbose_name_plural = 'Tipos de Contrato'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Contrato(models.Model):
    """Contrato legal detallado que vincula un inmueble con un inquilino/comprador."""

    class EstadoContrato(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        ENVIADO = 'enviado', 'Enviado al cliente'
        ACEPTADO = 'aceptado', 'Aceptado por el cliente'
        RECHAZADO = 'rechazado', 'Rechazado por el cliente'
        ACTIVO = 'activo', 'Activo'
        FINALIZADO = 'finalizado', 'Finalizado'
        CANCELADO = 'cancelado', 'Cancelado'
        PENDIENTE = 'pendiente', 'Pendiente'

    # ─── Partes del contrato ─────────────────────────────────
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='contratos',
    )
    tipo_contrato = models.ForeignKey(
        TipoContrato,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contratos',
    )
    inquilino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contratos_inquilino',
    )

    # ─── Datos económicos ────────────────────────────────────
    inicio = models.DateField()
    fin = models.DateField(null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=10, default='USD')
    deposito = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dia_pago = models.PositiveIntegerField(default=1, help_text='Día del mes para pago (1-28)')
    forma_pago = models.CharField(max_length=100, default='Stripe / Transferencia', blank=True)

    # ─── Detalles legales ────────────────────────────────────
    clausulas = models.TextField(
        blank=True,
        help_text='Cláusulas adicionales del contrato'
    )
    condiciones_uso = models.TextField(
        blank=True,
        help_text='Condiciones de uso del inmueble'
    )
    penalidades = models.TextField(
        blank=True,
        help_text='Penalidades por incumplimiento'
    )
    politica_cancelacion = models.TextField(
        blank=True,
        help_text='Política de cancelación anticipada'
    )
    incluye_servicios = models.TextField(
        blank=True,
        help_text='Servicios incluidos (agua, luz, internet, etc.)'
    )
    restricciones = models.TextField(
        blank=True,
        help_text='Restricciones (mascotas, subarriendo, etc.)'
    )
    antecedentes = models.TextField(
        blank=True,
        help_text='Contexto previo, situación legal y antecedentes del inmueble'
    )
    uso_exclusivo = models.TextField(
        blank=True,
        help_text='Uso permitido del inmueble (vivienda, comercial, mixto, etc.)'
    )
    clausulas_especiales = models.TextField(
        blank=True,
        help_text='Cláusulas especiales adicionales pactadas entre las partes'
    )

    # ─── Estado y seguimiento ────────────────────────────────
    estado = models.CharField(
        max_length=20,
        choices=EstadoContrato.choices,
        default=EstadoContrato.BORRADOR,
    )
    observaciones = models.TextField(blank=True)
    motivo_rechazo = models.TextField(blank=True, help_text='Motivo si el cliente rechaza')
    chat = models.ForeignKey(
        'usuarios.Chat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contratos_chat',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inmuebles_contrato'
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-creado']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Guardar en base de datos primero
        super().save(*args, **kwargs)
        
        # Sincronización asíncrona a Blockchain
        try:
            from .blockchain_service import BlockchainService
            import hashlib
            
            # 1. Si es un nuevo contrato, registrar borrador en Ledger
            if is_new:
                BlockchainService.registrar_contrato(
                    contrato_id=self.id,
                    inmueble_id=self.inmueble.id,
                    propietario_id=self.inmueble.propietario.id,
                    inquilino_id=self.inquilino.id,
                    monto=self.monto,
                    deposito=self.deposito,
                    inicio_str=self.inicio,
                    fin_str=self.fin
                )
            
            # 2. Si el contrato pasa a activo o aceptado, registrar firmas criptográficas simuladas de las partes
            if self.estado in ['activo', 'aceptado']:
                hash_propietario = hashlib.sha256(f"PROPIETARIO-{self.id}-{self.inmueble.propietario.id}".encode()).hexdigest()
                hash_inquilino = hashlib.sha256(f"INQUILINO-{self.id}-{self.inquilino.id}".encode()).hexdigest()
                
                BlockchainService.registrar_firma_contrato(self.id, 'propietario', hash_propietario)
                BlockchainService.registrar_firma_contrato(self.id, 'inquilino', hash_inquilino)
                
            elif self.estado in ['finalizado', 'cancelado']:
                # Actualizar estado final en Blockchain
                BlockchainService._put("contratos/firmar", {
                    "id": f"CON-{self.id}",
                    "nuevoEstado": self.estado
                })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error sincronizando contrato {self.id} con Blockchain: {str(e)}")

    def __str__(self):
        return f'Contrato {self.id} — {self.inmueble.titulo}'


class Comision(models.Model):
    """Comisiones generadas por contratos."""
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name='comisiones',
    )
    pago = models.ForeignKey(
        'pagos.Pago',
        on_delete=models.CASCADE,
        related_name='comisiones',
        null=True,
        blank=True,
        help_text='Pago transaccional del cual se generó la comisión'
    )
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    pagada = models.BooleanField(default=True, help_text='Las comisiones transaccionales se asumen descontadas/pagadas al instante')
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'inmuebles_comision'
        verbose_name = 'Comisión'
        verbose_name_plural = 'Comisiones'
        ordering = ['-fecha']

    def __str__(self):
        return f'Comisión {self.porcentaje}% — Contrato {self.contrato.id}'


class Favorito(models.Model):
    """Inmuebles marcados como favoritos por los usuarios."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favoritos',
    )
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='favoritos_por_usuarios',
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inmuebles_favorito'
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ('usuario', 'inmueble')
        ordering = ['-creado']

    def __str__(self):
        return f'{self.usuario.username} — {self.inmueble.titulo}'
class Cita(models.Model):
    """Cita/visita agendada entre un cliente y un propietario para ver un inmueble."""

    class EstadoCita(models.TextChoices):
        PENDIENTE   = 'pendiente',  'Pendiente'
        CONFIRMADA  = 'confirmada', 'Confirmada'
        CANCELADA   = 'cancelada',  'Cancelada'
        COMPLETADA  = 'completada', 'Completada'

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='citas',
    )
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='citas_como_cliente',
    )
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='citas_como_propietario',
    )
    fecha       = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    estado = models.CharField(
        max_length=20, choices=EstadoCita.choices, default=EstadoCita.PENDIENTE,
    )
    notas   = models.TextField(blank=True)
    creado  = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'inmuebles_cita'
        verbose_name    = 'Cita'
        verbose_name_plural = 'Citas'
        ordering        = ['-fecha', '-hora_inicio']
        unique_together = ('inmueble', 'fecha', 'hora_inicio')

    def __str__(self):
        return f'Cita {self.fecha} {self.hora_inicio} — {self.inmueble.titulo}'


class HorarioDisponible(models.Model):
    """Horario semanal que el propietario define para recibir visitas."""

    DIAS_SEMANA = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='horarios_disponibles',
    )
    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='horarios_disponibles',
        null=True, blank=True,
        help_text='Si es nulo, aplica a todos los inmuebles del propietario',
    )
    dia_semana  = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    activo      = models.BooleanField(default=True)

    class Meta:
        db_table        = 'inmuebles_horario_disponible'
        verbose_name    = 'Horario Disponible'
        verbose_name_plural = 'Horarios Disponibles'
        ordering        = ['dia_semana', 'hora_inicio']

    def __str__(self):
        return f'{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}'


class VerificacionTitulo(models.Model):
    """Verificación legal de título de propiedad de un inmueble mediante IA (OCR + NLP)."""

    class EstadoVerificacion(models.TextChoices):
        PENDIENTE   = 'pendiente',   'Pendiente'
        PROCESANDO  = 'procesando',  'Procesando'
        VERIFICADO  = 'verificado',  'Verificado'
        OBSERVADO   = 'observado',   'Con Observaciones'
        RECHAZADO   = 'rechazado',   'No Válido'
        ERROR       = 'error',       'Error de Procesamiento'

    inmueble = models.OneToOneField(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='verificacion_titulo',
    )
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verificaciones_solicitadas',
    )
    archivo_titulo = models.CharField(max_length=500, help_text='URL de Cloudinary del documento subido')
    texto_ocr = models.TextField(blank=True, help_text='Texto extraído del documento')
    resultado_ia = models.JSONField(null=True, blank=True, help_text='Resultado del análisis legal de Groq en formato JSON')
    estado = models.CharField(
        max_length=20,
        choices=EstadoVerificacion.choices,
        default=EstadoVerificacion.PENDIENTE,
    )
    score_confianza = models.PositiveIntegerField(null=True, blank=True, help_text='Puntaje de confianza de 0 a 100')
    resumen_publico = models.TextField(blank=True, help_text='Resumen corto visible al público')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inmuebles_verificacion_titulo'
        verbose_name = 'Verificación de Título'
        verbose_name_plural = 'Verificaciones de Títulos'
        ordering = ['-creado']

    def save(self, *args, **kwargs):
        # Primero guardamos en la base de datos local
        super().save(*args, **kwargs)
        
        # Sincronización asíncrona a Blockchain si fue verificado con éxito
        if self.estado == 'verificado':
            try:
                from .blockchain_service import BlockchainService
                import hashlib
                
                # Calculamos un hash único del archivo de título
                hash_titulo = hashlib.sha256(self.archivo_titulo.encode('utf-8')).hexdigest()
                
                # Obtener dirección del inmueble
                dir_str = str(self.inmueble.direccion) if self.inmueble.direccion else "Sin dirección"
                
                BlockchainService.registrar_inmueble(
                    inmueble_id=self.inmueble.id,
                    titulo=self.inmueble.titulo,
                    propietario_id=self.inmueble.propietario.id,
                    direccion_str=dir_str,
                    hash_titulo=hash_titulo
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error sincronizando título {self.id} con Blockchain: {str(e)}")

    def __str__(self):
        return f'Verificación {self.estado} — {self.inmueble.titulo}'


class AccesoRecorrido360(models.Model):
    """Acceso temporal otorgado por un propietario a un cliente para un recorrido 360°."""
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name='accesos_360'
    )
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accesos_360_recibidos'
    )
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accesos_360_otorgados'
    )
    chat = models.ForeignKey(
        'usuarios.Chat',
        on_delete=models.CASCADE,
        related_name='accesos_360',
        null=True,
        blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activo = models.BooleanField(default=True)
    visitas = models.IntegerField(default=0)
    ultimo_acceso_visor = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'inmuebles_acceso_recorrido_360'
        verbose_name = 'Acceso a Recorrido 360°'
        verbose_name_plural = 'Accesos a Recorridos 360°'
        ordering = ['-creado']

    @property
    def es_valido(self) -> bool:
        from django.utils import timezone
        return self.activo and self.fecha_expiracion > timezone.now()

    def __str__(self):
        return f'Acceso: {self.cliente.email} -> {self.inmueble.titulo} (Exp: {self.fecha_expiracion})'


