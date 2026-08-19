from .models import TipoContrato, Contrato, VerificacionTitulo


def get_tipos_contrato_for_select():
    """Get all tipos de contrato for select dropdown."""
    return TipoContrato.objects.values('id', 'nombre').order_by('nombre')


def get_all_tipos_contrato():
    """Get all tipos de contrato."""
    return TipoContrato.objects.all().order_by('nombre')


def get_contrato_with_details(contrato_id):
    """Get a contrato with all related details."""
    return Contrato.objects.select_related(
        'inmueble', 
        'inmueble__propietario', 
        'inmueble__direccion',
        'tipo_contrato', 
        'inquilino'
    ).prefetch_related('inmueble__multimedia').get(id=contrato_id)


def get_contratos_for_user(user):
    """Get all contratos for a specific user (either as propietario or inquilino)."""
    from django.db.models import Q
    return Contrato.objects.select_related(
        'inmueble', 
        'inmueble__propietario',
        'inmueble__direccion',
        'tipo_contrato', 
        'inquilino'
    ).filter(
        Q(inquilino=user) | Q(inmueble__propietario=user)
    ).order_by('-creado')



def get_contrato_pdf_data(contrato_id):
    """Get all data needed for PDF generation."""
    contrato = get_contrato_with_details(contrato_id)
    return {
        'contrato_id': contrato.id,
        'inmueble_titulo': contrato.inmueble.titulo,
        'inmueble_direccion': contrato.inmueble.direccion,
        'propietario_nombre': contrato.inmueble.propietario.get_full_name(),
        'propietario_ci': contrato.inmueble.propietario.ci,
        'inquilino_nombre': contrato.inquilino.get_full_name(),
        'inquilino_ci': contrato.inquilino.ci,
        'tipo_contrato': contrato.tipo_contrato.nombre if contrato.tipo_contrato else '',
        'monto': contrato.monto,
        'moneda': contrato.moneda,
        'inicio': contrato.inicio,
        'fin': contrato.fin,
        'deposito': contrato.deposito,
        'dia_pago': contrato.dia_pago,
        'clausulas': contrato.clausulas,
        'condiciones_uso': contrato.condiciones_uso,
        'penalidades': contrato.penalidades,
        'politica_cancelacion': contrato.politica_cancelacion,
        'incluye_servicios': contrato.incluye_servicios,
        'restricciones': contrato.restricciones,
        'observaciones': contrato.observaciones,
        'antecedentes': contrato.antecedentes,
        'uso_exclusivo': contrato.uso_exclusivo,
        'clausulas_especiales': contrato.clausulas_especiales,
    }

def get_datos_contrato_para_ia(contrato_id: int, usuario) -> dict:
    """Extrae datos limpios para inyectarlos como contexto a la IA."""
    contrato = get_contrato_with_details(contrato_id)
    
    # Validar que el usuario tenga permisos (opcional a nivel de selector, pero útil)
    # Asumimos que la vista ya filtró si puede acceder, pero obtenemos la data cruda.
    
    dir_inm = contrato.inmueble.direccion
    direccion_str = f"{dir_inm.calle}, Zona {dir_inm.zona}, {dir_inm.ciudad}" if dir_inm else "No especificada"
    
    return {
        "tipo_contrato": contrato.tipo_contrato.nombre if contrato.tipo_contrato else "Contrato de Arrendamiento",
        "fecha_inicio": str(contrato.inicio),
        "fecha_fin": str(contrato.fin) if contrato.fin else "Indefinido",
        "monto": float(contrato.monto),
        "moneda": contrato.moneda,
        "dia_pago": contrato.dia_pago,
        "deposito": float(contrato.deposito),
        "inmueble": {
            "titulo": contrato.inmueble.titulo,
            "direccion": direccion_str,
            "superficie": float(contrato.inmueble.superficie) if contrato.inmueble.superficie else "No especificada"
        },
        "propietario": {
            "nombre": contrato.inmueble.propietario.get_full_name(),
            "ci": getattr(contrato.inmueble.propietario, 'ci', 'N/A'),
            "telefono": getattr(contrato.inmueble.propietario, 'telefono', 'N/A') or 'N/A',
        },
        "inquilino": {
            "nombre": contrato.inquilino.get_full_name(),
            "ci": getattr(contrato.inquilino, 'ci', 'N/A'),
            "telefono": getattr(contrato.inquilino, 'telefono', 'N/A') or 'N/A',
        },
        "clausulas_adicionales": contrato.clausulas or "Ninguna",
        "clausulas_especiales": contrato.clausulas_especiales or "Ninguna",
        "penalidades": contrato.penalidades or "Ninguna",
        "antecedentes": contrato.antecedentes or "No especificado",
        "uso_exclusivo": contrato.uso_exclusivo or "No especificado",
        "condiciones_uso": contrato.condiciones_uso or "Ninguna",
        "politica_cancelacion": contrato.politica_cancelacion or "Ninguna",
        "incluye_servicios": contrato.incluye_servicios or "Ninguna",
        "restricciones": contrato.restricciones or "Ninguna",
    }


def get_verificacion_by_inmueble(inmueble_id: int):
    """Obtiene la verificación de título registrada para un inmueble, o retorna None."""
    try:
        return VerificacionTitulo.objects.get(inmueble_id=inmueble_id)
    except VerificacionTitulo.DoesNotExist:
        return None


def get_inmuebles_para_busqueda_mapa(tipo_oferta=None, precio_max=None):
    """
    Obtiene todos los inmuebles activos con coordenadas GPS válidas para filtrado espacial.
    """
    from .models import Inmueble, Publicacion
    qs = Inmueble.objects.select_related('direccion', 'propietario', 'tipo').prefetch_related(
        'multimedia', 'publicaciones'
    ).filter(
        estado=Inmueble.EstadoInmueble.DISPONIBLE,
        gps__isnull=False
    ).exclude(gps__exact='')

    if tipo_oferta or precio_max:
        pub_filter = {'estado': Publicacion.EstadoPublicacion.ACTIVA}
        if tipo_oferta:
            pub_filter['tipo_oferta'] = tipo_oferta
        if precio_max:
            pub_filter['precio__lte'] = precio_max
        qs = qs.filter(publicaciones__in=Publicacion.objects.filter(**pub_filter))

    return qs.distinct()


def get_inmuebles_para_busqueda_semantica(tipo_oferta=None, precio_max=None):
    """
    Obtiene todos los inmuebles activos con detalles completos para búsqueda semántica / multimodal.
    """
    from .models import Inmueble, Publicacion
    qs = Inmueble.objects.select_related('direccion', 'propietario', 'tipo').prefetch_related(
        'multimedia', 'publicaciones'
    ).filter(
        estado=Inmueble.EstadoInmueble.DISPONIBLE
    )

    if tipo_oferta or precio_max:
        pub_filter = {'estado': Publicacion.EstadoPublicacion.ACTIVA}
        if tipo_oferta:
            pub_filter['tipo_oferta'] = tipo_oferta
        if precio_max:
            pub_filter['precio__lte'] = precio_max
        qs = qs.filter(publicaciones__in=Publicacion.objects.filter(**pub_filter))

    return qs.distinct()


def punto_dentro_de_poligono(lat: float, lng: float, poligono: list) -> bool:
    """
    Verifica si un punto (lat, lng) se encuentra dentro de un polígono [[lat, lng], ...]
    utilizando el algoritmo Ray-Casting (filtrado espacial de zonas dibujadas).
    """
    if not poligono or len(poligono) < 3:
        return True

    dentro = False
    n = len(poligono)
    p1_lat, p1_lng = float(poligono[0][0]), float(poligono[0][1])

    for i in range(1, n + 1):
        p2_lat, p2_lng = float(poligono[i % n][0]), float(poligono[i % n][1])
        if min(p1_lng, p2_lng) < lng <= max(p1_lng, p2_lng):
            if lat <= max(p1_lat, p2_lat):
                if p1_lng != p2_lng:
                    x_inters = (lng - p1_lng) * (p2_lat - p1_lat) / (p2_lng - p1_lng) + p1_lat
                if p1_lat == p2_lat or lat <= x_inters:
                    dentro = not dentro
        p1_lat, p1_lng = p2_lat, p2_lng

    return dentro



