import stripe
import json
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import TipoPago, Pago, DetallePago, HistorialPago, TipoPlan, Plan, TransaccionStripe, ConfiguracionSistema
from .serializers import (
    TipoPagoSerializer,
    PagoSerializer,
    DetallePagoSerializer,
    HistorialPagoSerializer,
    TipoPlanSerializer,
    PlanSerializer,
    TransaccionStripeSerializer,
)
from inmuebles.models import Contrato, Inmueble
from usuarios.models import Mensaje, Chat, Notificacion
from .services.comisiones_service import calcular_y_generar_comision

stripe.api_key = settings.STRIPE_SECRET_KEY


class TipoPagoViewSet(viewsets.ModelViewSet):
    """CRUD para tipos de pago."""
    queryset = TipoPago.objects.all()
    serializer_class = TipoPagoSerializer


class PagoViewSet(viewsets.ModelViewSet):
    """CRUD para pagos."""
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Pago.objects.select_related('contrato', 'tipo_pago', 'usuario').prefetch_related('detalles')
        if not user.is_authenticated: return qs.none()
        if (user.is_staff or user.rol == 'admin') and self.request.query_params.get('personal') != 'true':
            return qs.all()
        # Dueño del pago o dueño del inmueble asociado al contrato
        from django.db.models import Q
        return qs.filter(Q(usuario=user) | Q(contrato__inmueble__propietario=user))

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class DetallePagoViewSet(viewsets.ModelViewSet):
    """CRUD para detalles de pago."""
    queryset = DetallePago.objects.select_related('pago').all()
    serializer_class = DetallePagoSerializer


class HistorialPagoViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura para historial de pagos."""
    queryset = HistorialPago.objects.all()
    serializer_class = HistorialPagoSerializer

    def get_queryset(self):
        user = self.request.user
        qs = HistorialPago.objects.select_related('pago', 'usuario')
        if not user.is_authenticated: return qs.none()
        if (user.is_staff or user.rol == 'admin') and self.request.query_params.get('personal') != 'true':
            return qs.all()
        # Solo lo relacionado a sus propios pagos
        from django.db.models import Q
        return qs.filter(Q(pago__usuario=user) | Q(pago__contrato__inmueble__propietario=user))


class TipoPlanViewSet(viewsets.ModelViewSet):
    """CRUD para tipos de plan."""
    queryset = TipoPlan.objects.all()
    serializer_class = TipoPlanSerializer


class PlanViewSet(viewsets.ModelViewSet):
    """CRUD para planes."""
    queryset = Plan.objects.select_related('tipo_plan').all()
    serializer_class = PlanSerializer


# ═══════════════════════════════════════════════════════════════════
#   STRIPE — Pasarela de Pagos
# ═══════════════════════════════════════════════════════════════════

class CrearSesionStripeView(APIView):
    """
    RF-25: Integración de pasarela de pagos.
    Solo el propietario del inmueble puede crear una sesión de pago Stripe.
    Se envía el enlace de pago como mensaje en el chat.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        contrato_id = request.data.get('contrato_id')
        monto = request.data.get('monto')
        tipo_operacion = request.data.get('tipo_operacion', 'mensualidad')
        descripcion = request.data.get('descripcion', '')
        chat_id = request.data.get('chat_id')
        moneda = request.data.get('moneda', 'usd')

        # Validaciones
        if not contrato_id or not monto:
            return Response(
                {'error': 'contrato_id y monto son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            monto_decimal = Decimal(str(monto))
            if monto_decimal <= 0:
                raise ValueError()
        except (ValueError, Exception):
            return Response(
                {'error': 'Monto debe ser un número positivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar contrato y que el usuario sea el propietario
        try:
            contrato = Contrato.objects.select_related('inmueble', 'inquilino').get(id=contrato_id)
        except Contrato.DoesNotExist:
            return Response({'error': 'Contrato no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if contrato.inmueble.propietario != request.user:
            return Response(
                {'error': 'Solo el propietario puede enviar enlaces de pago'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Determinar descripción
        if not descripcion:
            tipo_labels = dict(TransaccionStripe.TipoOperacion.choices)
            descripcion = f'{tipo_labels.get(tipo_operacion, tipo_operacion)} — {contrato.inmueble.titulo}'

        # Crear sesión de Stripe Checkout
        try:
            # Monto en centavos para Stripe
            monto_centavos = int(monto_decimal * 100)

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': moneda,
                        'product_data': {
                            'name': f'{contrato.inmueble.titulo}',
                            'description': descripcion,
                        },
                        'unit_amount': monto_centavos,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{settings.FRONTEND_URL}/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{settings.FRONTEND_URL}/pago-cancelado?session_id={{CHECKOUT_SESSION_ID}}',
                metadata={
                    'contrato_id': str(contrato.id),
                    'pagador_id': str(contrato.inquilino.id),
                    'propietario_id': str(request.user.id),
                    'tipo_operacion': tipo_operacion,
                    'chat_id': str(chat_id) if chat_id else '',
                },
            )

            # Crear registro de transacción pendiente
            transaccion = TransaccionStripe.objects.create(
                contrato=contrato,
                pagador=contrato.inquilino,
                propietario=request.user,
                tipo_operacion=tipo_operacion,
                monto=monto_decimal,
                moneda=moneda,
                descripcion=descripcion,
                stripe_session_id=checkout_session.id,
                estado='pendiente',
                chat_id=chat_id if chat_id else None,
            )

            # Enviar mensaje en el chat con el enlace de pago
            if chat_id:
                try:
                    chat = Chat.objects.get(id=chat_id)
                    Mensaje.objects.create(
                        chat=chat,
                        remitente=request.user,
                        tipo='texto',
                        contenido=f'💳 SOLICITUD DE PAGO\n'
                                  f'Monto: ${monto_decimal} {moneda.upper()}\n'
                                  f'Concepto: {descripcion}\n'
                                  f'Propiedad: {contrato.inmueble.titulo}\n'
                                  f'───────────────\n'
                                  f'STRIPE_PAYMENT:{checkout_session.url}:TRANSACCION:{transaccion.id}:END',
                    )
                    chat.save()  # Update timestamp

                    # Notificar al pagador
                    from usuarios.services import crear_notificacion_sistema
                    crear_notificacion_sistema(
                        usuario=contrato.inquilino,
                        titulo='Solicitud de pago recibida',
                        mensaje=f'{request.user.get_full_name()} te ha enviado una solicitud de pago de ${monto_decimal} {moneda.upper()} por "{contrato.inmueble.titulo}".',
                        tipo=Notificacion.TipoNotificacion.PAGO,
                    )
                except Chat.DoesNotExist:
                    pass

            return Response({
                'session_id': checkout_session.id,
                'checkout_url': checkout_session.url,
                'transaccion_id': transaccion.id,
            }, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Error de Stripe: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ConfirmarPagoStripeView(APIView):
    """
    RF-24: Gestionar Pago.
    Confirma el estado de un pago tras la redirección de Stripe.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaccion = TransaccionStripe.objects.select_related(
                'contrato', 'contrato__inmueble', 'contrato__tipo_contrato',
                'pagador', 'propietario'
            ).get(stripe_session_id=session_id)
        except TransaccionStripe.DoesNotExist:
            return Response({'error': 'Transacción no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Consultar Stripe por el estado real
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if session.payment_status == 'paid' and transaccion.estado == 'pendiente':
            transaccion.estado = 'completada'
            transaccion.stripe_payment_intent = session.payment_intent or ''

            # Obtener el receipt URL del payment intent
            if session.payment_intent:
                try:
                    pi = stripe.PaymentIntent.retrieve(session.payment_intent)
                    if pi.latest_charge:
                        charge = stripe.Charge.retrieve(pi.latest_charge)
                        transaccion.comprobante_url = charge.receipt_url or ''
                except Exception:
                    pass

            transaccion.save()

            # RF-24: Actualizar estado del inmueble y contrato
            contrato = transaccion.contrato
            inmueble = contrato.inmueble
            tipo_contrato_nombre = (contrato.tipo_contrato.nombre.lower() if contrato.tipo_contrato else '')

            if transaccion.tipo_operacion == 'compra' or 'venta' in tipo_contrato_nombre:
                inmueble.estado = 'ocupado'
                inmueble.save()
                contrato.estado = 'activo'
                contrato.save()
            elif transaccion.tipo_operacion in ['alquiler', 'mensualidad', 'deposito']:
                if inmueble.estado == 'disponible':
                    inmueble.estado = 'ocupado'
                    inmueble.save()
                if contrato.estado == 'pendiente':
                    contrato.estado = 'activo'
                    contrato.save()

            # RF-26: Crear registro de Pago formal vinculado
            tipo_pago_stripe, _ = TipoPago.objects.get_or_create(
                nombre='Stripe',
                defaults={'descripcion': 'Pago procesado por Stripe', 'activo': True}
            )
            pago = Pago.objects.create(
                contrato=contrato,
                tipo_pago=tipo_pago_stripe,
                usuario=transaccion.pagador,
                monto=transaccion.monto,
                fecha=transaccion.creado.date(),
                referencia=f'stripe:{transaccion.stripe_session_id}',
                estado='completado',
                observaciones=f'Pago procesado por Stripe. Transacción #{transaccion.id}. {transaccion.descripcion}',
            )

            # Generar comisión transaccional de forma automática
            calcular_y_generar_comision(pago)

            # RF-26: Crear historial de pago
            HistorialPago.objects.create(
                pago=pago,
                anterior='pendiente',
                nuevo='completado',
                comentario=f'Pago completado exitosamente vía Stripe. Session: {session_id}',
                usuario=transaccion.pagador,
            )

            # Notificaciones
            from usuarios.services import crear_notificacion_sistema
            crear_notificacion_sistema(
                usuario=transaccion.propietario,
                titulo='Pago recibido ✅',
                mensaje=f'{transaccion.pagador.get_full_name()} ha completado el pago de ${transaccion.monto} {transaccion.moneda.upper()} por "{inmueble.titulo}".',
                tipo=Notificacion.TipoNotificacion.PAGO,
            )
            crear_notificacion_sistema(
                usuario=transaccion.pagador,
                titulo='Pago procesado exitosamente ✅',
                mensaje=f'Tu pago de ${transaccion.monto} {transaccion.moneda.upper()} por "{inmueble.titulo}" ha sido procesado correctamente.',
                tipo=Notificacion.TipoNotificacion.PAGO,
            )

            # Enviar mensaje de confirmación en el chat
            if transaccion.chat:
                Mensaje.objects.create(
                    chat=transaccion.chat,
                    remitente=transaccion.pagador,
                    tipo='texto',
                    contenido=f'✅ PAGO COMPLETADO\n'
                              f'Monto: ${transaccion.monto} {transaccion.moneda.upper()}\n'
                              f'Concepto: {transaccion.descripcion}\n'
                              f'Estado: Completado\n'
                              f'STRIPE_RECEIPT:{transaccion.comprobante_url}:END',
                )
                transaccion.chat.save()

        elif session.payment_status == 'unpaid':
            if transaccion.estado == 'pendiente':
                transaccion.estado = 'cancelada'
                transaccion.save()

        serializer = TransaccionStripeSerializer(transaccion)
        return Response(serializer.data)


class TransaccionStripeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    RF-26: Gestión de historial de transacciones y emisión de comprobantes.
    Listado y detalle de transacciones Stripe.
    """
    serializer_class = TransaccionStripeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = TransaccionStripe.objects.select_related(
            'contrato', 'contrato__inmueble', 'pagador', 'propietario'
        )
        if user.is_staff or user.rol == 'admin':
            return qs.all()
        return qs.filter(Q(pagador=user) | Q(propietario=user))

    @action(detail=True, methods=['get'], url_path='comprobante')
    def comprobante(self, request, pk=None):
        """Obtiene el comprobante/recibo de Stripe para una transacción."""
        transaccion = self.get_object()
        if transaccion.comprobante_url:
            return Response({'comprobante_url': transaccion.comprobante_url})

        # Intentar obtener desde Stripe si no lo tenemos
        if transaccion.stripe_payment_intent:
            try:
                pi = stripe.PaymentIntent.retrieve(transaccion.stripe_payment_intent)
                if pi.latest_charge:
                    charge = stripe.Charge.retrieve(pi.latest_charge)
                    if charge.receipt_url:
                        transaccion.comprobante_url = charge.receipt_url
                        transaccion.save()
                        return Response({'comprobante_url': charge.receipt_url})
            except Exception:
                pass

        return Response({'comprobante_url': None, 'mensaje': 'Comprobante no disponible'})


class ContratosParaPagoView(APIView):
    """
    Devuelve los contratos activos de un inmueble vinculado
    a un chat, para que el propietario pueda seleccionar cuál
    contrato cobrar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        chat_id = request.query_params.get('chat_id')
        inmueble_id = request.query_params.get('inmueble_id')

        user = request.user
        qs = Contrato.objects.select_related('inmueble', 'inquilino', 'tipo_contrato')

        if inmueble_id:
            qs = qs.filter(inmueble_id=inmueble_id, inmueble__propietario=user)
        elif chat_id:
            try:
                chat = Chat.objects.get(id=chat_id)
                if chat.inmueble:
                    qs = qs.filter(inmueble=chat.inmueble, inmueble__propietario=user)
                else:
                    # Buscar contratos donde el otro participante es inquilino
                    other_user_id = chat.participante2_id if chat.participante1 == user else chat.participante1_id
                    qs = qs.filter(inmueble__propietario=user, inquilino_id=other_user_id)
            except Chat.DoesNotExist:
                return Response([])
        else:
            qs = qs.filter(inmueble__propietario=user)

        contratos = []
        for c in qs:
            contratos.append({
                'id': c.id,
                'inmueble_titulo': c.inmueble.titulo,
                'inmueble_id': c.inmueble.id,
                'inquilino_nombre': c.inquilino.get_full_name(),
                'inquilino_id': c.inquilino.id,
                'tipo_contrato': c.tipo_contrato.nombre if c.tipo_contrato else 'Sin tipo',
                'monto': str(c.monto),
                'estado': c.estado,
                'inicio': str(c.inicio),
                'fin': str(c.fin) if c.fin else None,
            })

        return Response(contratos)


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def stripe_webhook(request):
    """
    Webhook de Stripe para manejar eventos de pago.
    Actualiza automáticamente el estado de la transacción
    cuando Stripe confirma el pago.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    # Si tenemos webhook secret configurado, verificar la firma
    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)
    else:
        # En desarrollo, simplemente parsear el body
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

    # Procesar eventos
    event_type = event.get('type', '')

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id')

        try:
            transaccion = TransaccionStripe.objects.select_related(
                'contrato', 'contrato__inmueble', 'contrato__tipo_contrato',
                'pagador', 'propietario'
            ).get(stripe_session_id=session_id)

            if transaccion.estado == 'pendiente':
                transaccion.estado = 'completada'
                transaccion.stripe_payment_intent = session.get('payment_intent', '')
                transaccion.save()

                contrato = transaccion.contrato
                inmueble = contrato.inmueble
                tipo_contrato_nombre = (contrato.tipo_contrato.nombre.lower() if contrato.tipo_contrato else '')

                if transaccion.tipo_operacion == 'compra' or 'venta' in tipo_contrato_nombre:
                    inmueble.estado = 'ocupado'
                    inmueble.save()
                    contrato.estado = 'activo'
                    contrato.save()
                elif transaccion.tipo_operacion in ['alquiler', 'mensualidad', 'deposito']:
                    if inmueble.estado == 'disponible':
                        inmueble.estado = 'ocupado'
                        inmueble.save()
                    if contrato.estado == 'pendiente':
                        contrato.estado = 'activo'
                        contrato.save()

                # Crear pago formal
                tipo_pago_stripe, _ = TipoPago.objects.get_or_create(
                    nombre='Stripe',
                    defaults={'descripcion': 'Pago procesado por Stripe', 'activo': True}
                )
                pago = Pago.objects.create(
                    contrato=contrato,
                    tipo_pago=tipo_pago_stripe,
                    usuario=transaccion.pagador,
                    monto=transaccion.monto,
                    fecha=transaccion.creado.date(),
                    referencia=f'stripe:{session_id}',
                    estado='completado',
                    observaciones=f'Webhook Stripe. Transacción #{transaccion.id}.',
                )
                # Generar comisión transaccional de forma automática
                calcular_y_generar_comision(pago)
                HistorialPago.objects.create(
                    pago=pago,
                    anterior='pendiente',
                    nuevo='completado',
                    comentario=f'Confirmado por webhook. Session: {session_id}',
                    usuario=transaccion.pagador,
                )

                # --- Enviar Mensaje al Chat con Comprobante ---
                # Buscamos el chat asociado al inmueble y los participantes
                try:
                    chat = Chat.objects.filter(
                        Q(participante1=transaccion.pagador, participante2=transaccion.propietario) |
                        Q(participante1=transaccion.propietario, participante2=transaccion.pagador),
                        inmueble=inmueble
                    ).first()

                    if chat:
                        receipt_url = session.get('receipt_url', '')
                        contenido = (
                            f"CONFIRMACION DE PAGO\n"
                            f"Se ha procesado exitosamente el pago por la propiedad: {inmueble.titulo}.\n"
                            f"Monto: {transaccion.monto} BOB.\n"
                            f"Estado: Completado\n"
                            f"STRIPE_RECEIPT:{receipt_url}:END"
                        )
                        Mensaje.objects.create(
                            chat=chat,
                            remitente=transaccion.propietario, # Enviado por el sistema/propietario
                            tipo='texto',
                            contenido=contenido
                        )
                        
                        # Notificacion al cliente
                        Notificacion.objects.create(
                            usuario=transaccion.pagador,
                            tipo='pago',
                            titulo='Pago Confirmado',
                            mensaje=f'Tu pago por {inmueble.titulo} ha sido procesado exitosamente.'
                        )
                except Exception as e:
                    print(f"Error enviando mensaje de chat post-pago: {e}")

        except TransaccionStripe.DoesNotExist:
            pass

    return HttpResponse(status=200)

class IsAdminOrStaffUser(permissions.BasePermission):
    """Permiso para usuarios administradores (rol admin o is_staff)."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or getattr(request.user, 'rol', None) == 'admin')
        )


class ConfiguracionSistemaViewSet(viewsets.ModelViewSet):
    """CRUD para la configuración global del sistema (Porcentaje de Comisión)."""
    from .serializers import ConfiguracionSistemaSerializer
    serializer_class = ConfiguracionSistemaSerializer
    permission_classes = [IsAdminOrStaffUser]

    def get_queryset(self):
        # Aseguramos que siempre exista al menos una configuración al consultar/modificar
        ConfiguracionSistema.get_config()
        return ConfiguracionSistema.objects.all()


class ReportesAPIView(APIView):
    """API para obtener reportes y métricas dinámicas."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .services.reportes_service import obtener_estadisticas_admin, obtener_balance_propietario
        
        filtros = {
            'rango': request.query_params.get('rango'),
            'fecha_inicio': request.query_params.get('fecha_inicio'),
            'fecha_fin': request.query_params.get('fecha_fin'),
            'tipo_contrato': request.query_params.get('tipo_contrato'),
            'inmueble_id': request.query_params.get('inmueble_id'),
            'anio': request.query_params.get('anio'),
            'mes': request.query_params.get('mes'),
            'ciudad': request.query_params.get('ciudad'),
        }

        if (request.user.rol == 'admin' or request.user.is_staff) and request.query_params.get('personal') != 'true':
            # Vista Administrador
            data = obtener_estadisticas_admin(filtros)
            return Response(data)
        else:
            # Vista Propietario
            data = obtener_balance_propietario(request.user, filtros)
            return Response(data)
