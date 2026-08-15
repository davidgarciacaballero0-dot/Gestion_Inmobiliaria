from decimal import Decimal
from inmuebles.models import Comision
from pagos.models import Pago, ConfiguracionSistema

def calcular_y_generar_comision(pago: Pago) -> Comision:
    """
    Calcula y registra la comisión para un pago confirmado.
    Utiliza el porcentaje configurado globalmente en el sistema.
    """
    # Obtener configuración global (Singleton)
    config = ConfiguracionSistema.get_config()
    porcentaje_base = config.porcentaje_comision_plataforma

    # Calcular monto de la comisión
    monto_comision = pago.monto * (Decimal(porcentaje_base) / Decimal('100'))
    
    # Redondear a 2 decimales
    monto_comision = round(monto_comision, 2)

    # Crear el registro de comisión
    comision = Comision.objects.create(
        contrato=pago.contrato,
        pago=pago,
        porcentaje=porcentaje_base,
        monto=monto_comision,
        descripcion=f"Comisión automática del {porcentaje_base}% por pago #{pago.id}",
        pagada=True # Las comisiones de pagos en línea se asumen descontadas al instante
    )
    
    return comision
