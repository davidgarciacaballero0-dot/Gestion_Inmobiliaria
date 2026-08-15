from django.db import transaction
from django.db.models import Q
from .models import TipoContrato, Contrato, VerificacionTitulo, Inmueble
from django.core.exceptions import ValidationError


def get_tipo_contrato_by_id(tipo_contrato_id):
    """Get a tipo contrato by ID."""
    try:
        return TipoContrato.objects.get(id=tipo_contrato_id)
    except TipoContrato.DoesNotExist:
        return None


# def get_all_tipos_contrato() moved to selectors.py


def create_tipo_contrato(*, nombre, descripcion=''):
    """Create a new tipo contrato."""
    return TipoContrato.objects.create(
        nombre=nombre,
        descripcion=descripcion
    )


def update_tipo_contrato(tipo_contrato, *, nombre, descripcion=''):
    """Update an existing tipo contrato."""
    tipo_contrato.nombre = nombre
    tipo_contrato.descripcion = descripcion
    tipo_contrato.save()
    return tipo_contrato


@transaction.atomic
def delete_tipo_contrato(tipo_contrato_id):
    """Delete a tipo contrato, checking for referential integrity.
    
    Raises:
        ValidationError: If the tipo contrato is referenced by existing contracts.
    """
    tipo_contrato = get_tipo_contrato_by_id(tipo_contrato_id)
    if not tipo_contrato:
        raise ValidationError("Tipo de contrato no encontrado.")
    
    # Check if there are any contracts referencing this tipo contrato
    contracts_count = Contrato.objects.filter(tipo_contrato=tipo_contrato).count()
    if contracts_count > 0:
        raise ValidationError(
            f"No se puede eliminar este tipo de contrato porque está referenciado "
            f"por {contracts_count} contrato(s) existente(s)."
        )
    
    tipo_contrato.delete()


from django.template.loader import render_to_string
import tempfile
from .selectors import get_contrato_pdf_data

def generate_contract_pdf(contrato_id):
    """Generate a PDF for a contract using xhtml2pdf.
    
    Args:
        contrato_id: ID of the contract to generate PDF for
        
    Returns:
        bytes: PDF content as bytes
    """
    from xhtml2pdf import pisa
    from io import BytesIO
    
    context = get_contrato_pdf_data(contrato_id)
    html_string = render_to_string('contratos/pdf_template.html', context)
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    else:
        raise Exception(f"Error generando PDF: {pdf.err}")


import json
import requests
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from .selectors import get_datos_contrato_para_ia

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generar_contrato_pdf_con_ia(contrato_id: int, usuario, instrucciones_usuario: str = '') -> bytes:
    """Genera un PDF del contrato con IA (Groq) y diseño profesional tipo notarial.
    
    Args:
        contrato_id: ID del contrato
        usuario: Usuario que solicita la generación
        instrucciones_usuario: Texto libre del usuario (escrito o transcrito de audio)
            con indicaciones adicionales para el contrato (antecedentes, cláusulas, etc.)
    """

    # 1. Obtener datos
    datos = get_datos_contrato_para_ia(contrato_id, usuario)
    
    # 2. Construir Prompt
    prompt = f"""
Actúa como un Abogado Inmobiliario Boliviano experto. Redacta el texto legal completo para un {datos['tipo_contrato']}.

DATOS DEL CONTRATO (usa estos datos exactamente, no modifiques nombres, fechas ni montos):
- Propietario: {datos['propietario']['nombre']} (CI: {datos['propietario']['ci']})
- Inquilino/Cliente: {datos['inquilino']['nombre']} (CI: {datos['inquilino']['ci']})
- Inmueble: {datos['inmueble']['titulo']} ubicado en {datos['inmueble']['direccion']} (Superficie: {datos['inmueble']['superficie']} m2)
- Fecha de Inicio: {datos['fecha_inicio']}
- Fecha de Fin: {datos['fecha_fin']}
- Monto: {datos['monto']} {datos['moneda']}
- Día de pago: {datos['dia_pago']} de cada mes
- Depósito de Garantía: {datos['deposito']} {datos['moneda']}
- Antecedentes: {datos['antecedentes']}
- Uso Exclusivo del Inmueble: {datos['uso_exclusivo']}
- Cláusulas Adicionales: {datos['clausulas_adicionales']}
- Cláusulas Especiales: {datos['clausulas_especiales']}
- Penalidades: {datos['penalidades']}
- Condiciones de Uso: {datos['condiciones_uso']}
- Política de Cancelación: {datos['politica_cancelacion']}
- Servicios Incluidos: {datos['incluye_servicios']}
- Restricciones: {datos['restricciones']}

INSTRUCCIONES DE FORMATO:
- El contrato DEBE incluir todas estas secciones en orden: ANTECEDENTES, OBJETO DEL CONTRATO, DURACIÓN, PRECIO Y FORMA DE PAGO, OBLIGACIONES DEL PROPIETARIO, OBLIGACIONES DEL ARRENDATARIO, GARANTÍA, USO DEL INMUEBLE, SERVICIOS INCLUIDOS, CLÁUSULAS ESPECIALES, PENALIDADES, POLÍTICA DE CANCELACIÓN, RESOLUCIÓN DEL CONTRATO, JURISDICCIÓN.
- Si un dato de la sección dice 'Ninguna', 'No especificado' o está vacío, redacta esa sección con texto legal estándar boliviano apropiado para ese tipo de contrato.
- Devuelve ÚNICAMENTE el texto legal del contrato listo para imprimir.
- NO incluyas saludos, explicaciones, ni bloques de código. NO uses formato Markdown (sin asteriscos, sin numerales).
- Usa un tono formal, legal y estructurado en párrafos claros. Separa cada sección con su título en MAYÚSCULAS seguido de dos saltos de línea.
"""

    # 2b. Inyectar instrucciones del usuario (texto libre o transcripción de audio)
    if instrucciones_usuario:
        prompt += f"""

INSTRUCCIONES ESPECIALES DEL CLIENTE (OBLIGATORIO INCORPORAR):
El cliente ha solicitado específicamente las siguientes condiciones adicionales. DEBES incorporarlas de forma legal y formal en las secciones correspondientes del contrato. Estas instrucciones tienen PRIORIDAD sobre el texto estándar de cada sección:

{instrucciones_usuario}

Por ejemplo: si el cliente pide "cláusula de renovación de 7 meses", debes redactar formalmente en la sección CLÁUSULAS ESPECIALES o DURACIÓN un texto legal que estipule la posibilidad de renovación por un período de 7 meses adicionales con las condiciones pertinentes.
"""

    # 3. Llamar a la API de Groq
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise Exception("La API Key de Groq no está configurada en el servidor.")
    headers_req = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Eres un Abogado Inmobiliario Boliviano experto en redacción de contratos. Tu objetivo es generar contratos legales precisos, formales y completos."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 4096
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers_req, timeout=60)
        resp.raise_for_status()
        texto_contrato = resp.json()['choices'][0]['message']['content']
    except Exception as e:
        error_msg = str(e)
        raise Exception(f"Error al generar contrato con Groq: {error_msg}")

    # Limpiar markdown residual
    texto_contrato = texto_contrato.replace('**', '').replace('##', '').replace('# ', '').replace('#', '')

    # 4. Generar PDF con diseño profesional notarial
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
    )

    # ── Paleta de colores ──────────────────────────────
    COLOR_PRIMARIO = colors.HexColor('#1a237e')   # Azul oscuro institucional
    COLOR_LINEA    = colors.HexColor('#424242')
    COLOR_GRIS     = colors.HexColor('#757575')

    # ── Estilos ────────────────────────────────────────
    styles = getSampleStyleSheet()

    st_encabezado = ParagraphStyle('Encabezado',
        parent=styles['Normal'], alignment=TA_CENTER,
        fontSize=9, textColor=COLOR_GRIS, leading=13)

    st_titulo_doc = ParagraphStyle('TituloDoc',
        parent=styles['Heading1'], alignment=TA_CENTER,
        fontSize=18, fontName='Helvetica-Bold',
        textColor=COLOR_PRIMARIO, spaceAfter=4, leading=22)

    st_subtitulo = ParagraphStyle('Subtitulo',
        parent=styles['Normal'], alignment=TA_CENTER,
        fontSize=10, textColor=COLOR_GRIS, spaceAfter=16, leading=14)

    st_seccion = ParagraphStyle('Seccion',
        parent=styles['Normal'], alignment=TA_LEFT,
        fontSize=10, fontName='Helvetica-Bold',
        textColor=COLOR_PRIMARIO, spaceBefore=14, spaceAfter=4, leading=14)

    st_parrafo = ParagraphStyle('Parrafo',
        parent=styles['Normal'], alignment=TA_JUSTIFY,
        fontSize=10, leading=15, spaceAfter=8, fontName='Helvetica')

    st_firma_nombre = ParagraphStyle('FirmaNombre',
        parent=styles['Normal'], alignment=TA_CENTER,
        fontSize=9, fontName='Helvetica-Bold', leading=13)

    st_firma_dato = ParagraphStyle('FirmaDato',
        parent=styles['Normal'], alignment=TA_CENTER,
        fontSize=8, textColor=COLOR_GRIS, leading=12)

    st_pie = ParagraphStyle('Pie',
        parent=styles['Normal'], alignment=TA_CENTER,
        fontSize=7, textColor=COLOR_GRIS, leading=11)

    # ── Construcción de elementos ──────────────────────
    elementos = []

    # Encabezado institucional
    elementos.append(Paragraph('"AÑO DE LA INTEGRACIÓN DIGITAL DE BOLIVIA"', st_encabezado))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARIO))
    elementos.append(Spacer(1, 0.4 * cm))

    # Título principal
    tipo_upper = datos['tipo_contrato'].upper()
    elementos.append(Paragraph(tipo_upper, st_titulo_doc))
    elementos.append(Paragraph(f'Contrato N.° {contrato_id:04d}', st_subtitulo))
    elementos.append(HRFlowable(width="100%", thickness=1, color=COLOR_LINEA))
    elementos.append(Spacer(1, 0.5 * cm))

    # ── Bloque de datos de las partes ─────────────────
    prop = datos['propietario']
    inq  = datos['inquilino']

    datos_partes = [
        [
            Paragraph('<b>PROPIETARIO</b>', ParagraphStyle('H', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, fontName='Helvetica-Bold', textColor=COLOR_PRIMARIO)),
            Paragraph('<b>ARRENDATARIO / COMPRADOR</b>', ParagraphStyle('H', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, fontName='Helvetica-Bold', textColor=COLOR_PRIMARIO))
        ],
        [
            Paragraph(f"{prop['nombre']}<br/><font color='grey' size='8'>CI: {prop['ci']} &nbsp;·&nbsp; Tel: {prop['telefono']}</font>", ParagraphStyle('C', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, leading=14)),
            Paragraph(f"{inq['nombre']}<br/><font color='grey' size='8'>CI: {inq['ci']} &nbsp;·&nbsp; Tel: {inq['telefono']}</font>", ParagraphStyle('C', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, leading=14)),
        ]
    ]

    tabla_partes = Table(datos_partes, colWidths=['50%', '50%'])
    tabla_partes.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#e8eaf6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('BOX',         (0, 0), (-1, -1), 0.8, COLOR_PRIMARIO),
        ('INNERGRID',   (0, 0), (-1, -1), 0.5, colors.HexColor('#c5cae9')),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',  (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    elementos.append(tabla_partes)
    elementos.append(Spacer(1, 0.5 * cm))

    # Datos del inmueble y condiciones
    inmueble = datos['inmueble']
    datos_contrato_tabla = [
        ['Inmueble', inmueble['titulo']],
        ['Dirección', inmueble['direccion']],
        ['Superficie', f"{inmueble['superficie']} m²"],
        ['Vigencia', f"{datos['fecha_inicio']}  →  {datos['fecha_fin']}"],
        ['Monto mensual', f"{datos['monto']} {datos['moneda']}"],
        ['Día de pago', f"Día {datos['dia_pago']} de cada mes"],
        ['Depósito / Garantía', f"{datos['deposito']} {datos['moneda']}"],
    ]

    st_lbl = ParagraphStyle('Lbl', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=COLOR_PRIMARIO)
    st_val = ParagraphStyle('Val', parent=styles['Normal'], fontSize=9, fontName='Helvetica')

    tabla_info = Table(
        [[Paragraph(r[0], st_lbl), Paragraph(r[1], st_val)] for r in datos_contrato_tabla],
        colWidths=[4 * cm, None]
    )
    tabla_info.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f5f5f5'), colors.white]),
        ('BOX',       (0, 0), (-1, -1), 0.6, COLOR_LINEA),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e0e0e0')),
        ('VALIGN',    (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.6 * cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINEA))
    elementos.append(Spacer(1, 0.4 * cm))

    # ── Cuerpo del contrato generado por IA ───────────
    lineas = texto_contrato.split('\n')
    for linea in lineas:
        limpia = linea.strip()
        if not limpia:
            continue
        # Detectar títulos de sección (líneas en MAYÚSCULAS o muy cortas)
        if limpia.isupper() and len(limpia) < 80:
            elementos.append(Paragraph(limpia, st_seccion))
        else:
            elementos.append(Paragraph(limpia, st_parrafo))

    # ── Bloque de firmas ───────────────────────────────
    elementos.append(Spacer(1, 1.5 * cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINEA))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph('FIRMAS DE LAS PARTES', st_seccion))
    elementos.append(Spacer(1, 1.8 * cm))

    linea_firma = '.' * 48

    firmas_data = [
        [
            Paragraph(linea_firma, ParagraphStyle('LF', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)),
            Paragraph(linea_firma, ParagraphStyle('LF', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)),
        ],
        [
            Paragraph(prop['nombre'].upper(), st_firma_nombre),
            Paragraph(inq['nombre'].upper(), st_firma_nombre),
        ],
        [
            Paragraph(f"CI: {prop['ci']}", st_firma_dato),
            Paragraph(f"CI: {inq['ci']}", st_firma_dato),
        ],
        [
            Paragraph('<b>PROPIETARIO</b>', st_firma_dato),
            Paragraph('<b>ARRENDATARIO / COMPRADOR</b>', st_firma_dato),
        ],
    ]

    tabla_firmas = Table(firmas_data, colWidths=['50%', '50%'])
    tabla_firmas.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(KeepTogether(tabla_firmas))

    # Pie de página
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_LINEA))
    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(Paragraph(
        f'Documento generado electrónicamente por Autogestión Inmobiliaria · Contrato N.° {contrato_id:04d} · {datos["fecha_inicio"]}',
        st_pie
    ))

    # ── Build ──────────────────────────────────────────
    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes



def chat_asistente_contrato(contrato_id: int, usuario, historial: list) -> str:
    """Chat interactivo con un asistente IA que actúa como abogado inmobiliario boliviano.

    Args:
        contrato_id: ID del contrato
        usuario: Usuario que hace la consulta
        historial: Lista de mensajes [{role: 'user'|'assistant', content: str}]

    Returns:
        str: Respuesta del asistente IA
    """
    datos = get_datos_contrato_para_ia(contrato_id, usuario)

    # System prompt con contexto completo del contrato
    system_prompt = f"""Eres un abogado especialista en derecho inmobiliario boliviano con 20 años de experiencia. 
Estás asesorando sobre el siguiente contrato de {datos['tipo_contrato']}:

DATOS DEL CONTRATO:
- Tipo: {datos['tipo_contrato']}
- Inmueble: {datos['inmueble']['titulo']} — {datos['inmueble']['direccion']} ({datos['inmueble']['superficie']} m²)
- Propietario: {datos['propietario']['nombre']} (CI: {datos['propietario']['ci']})
- Arrendatario/Comprador: {datos['inquilino']['nombre']} (CI: {datos['inquilino']['ci']})
- Monto: {datos['monto']} {datos['moneda']} mensuales
- Vigencia: desde {datos['fecha_inicio']} hasta {datos['fecha_fin']}
- Depósito de garantía: {datos['deposito']} {datos['moneda']}
- Día de pago: {datos['dia_pago']} de cada mes
- Antecedentes registrados: {datos.get('antecedentes', 'Ninguno')}
- Cláusulas especiales: {datos.get('clausulas_especiales', 'Ninguna')}
- Restricciones: {datos.get('restricciones', 'Ninguna')}
- Servicios incluidos: {datos.get('incluye_servicios', 'No especificado')}
- Uso exclusivo: {datos.get('uso_exclusivo', 'No especificado')}
- Penalidades: {datos.get('penalidades', 'Ninguna')}
- Política de cancelación: {datos.get('politica_cancelacion', 'No especificada')}

TU ROL:
- Analiza este contrato específico y da consejos personalizados basados en los datos reales
- Sugiere cláusulas concretas, restricciones y condiciones apropiadas para este caso
- Identifica posibles riesgos legales o vacíos contractuales
- Propón el texto legal formal cuando el usuario pida redactar algo
- Responde de forma clara, estructurada y en español boliviano formal
- Sé conciso pero completo. Usa listas cuando sea apropiado.
- NO inventes datos que no estén en el contrato
- Cuando sugieras cláusulas, formúlalas de manera que puedan copiarse directamente al contrato"""

    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise Exception("API Key de Groq no configurada en el servidor.")

    headers_req = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Construir messages: system + historial completo
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(historial)

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 1024,
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers_req, timeout=30)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                err_msg = f"{e.response.status_code} - {e.response.text}"
            except Exception:
                pass
        raise Exception(f"Error al contactar al asistente IA (Groq): {err_msg}")


def verificar_titulo_con_ia(inmueble_id: int, archivo_url: str, usuario, file_bytes: bytes = None) -> VerificacionTitulo:
    """Realiza la verificación de un título de propiedad mediante OCR e IA (Groq)."""
    import os
    import json
    import requests
    from io import BytesIO
    from PIL import Image
    import pytesseract
    from pdf2image import convert_from_bytes
    from django.conf import settings
    from usuarios.services import crear_notificacion_sistema
    from usuarios.models import Notificacion

    # 1. Obtener o crear el registro
    inmueble = Inmueble.objects.get(id=inmueble_id)
    verificacion, created = VerificacionTitulo.objects.get_or_create(
        inmueble=inmueble,
        defaults={
            'solicitado_por': usuario,
            'archivo_titulo': archivo_url,
            'estado': VerificacionTitulo.EstadoVerificacion.PROCESANDO
        }
    )
    if not created:
        verificacion.solicitado_por = usuario
        verificacion.archivo_titulo = archivo_url
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.PROCESANDO
        verificacion.save()

    texto_extraido = ""

    # Descargar el documento primero si no se proveen los bytes locales
    if not file_bytes:
        try:
            resp_file = requests.get(archivo_url, timeout=30)
            resp_file.raise_for_status()
            file_bytes = resp_file.content
        except Exception as exc:
            verificacion.estado = VerificacionTitulo.EstadoVerificacion.ERROR
            verificacion.resumen_publico = f"No se pudo descargar el documento. Verifique la URL y su conexión a internet."
            verificacion.texto_ocr = f"[ERROR DE DESCARGA]: {exc}"
            verificacion.save()
            return verificacion

    is_pdf = archivo_url.lower().endswith('.pdf') or b'%PDF' in file_bytes[:10]

    errores_extraccion = []  # Acumula errores de cada estrategia para logging

    # ── ESTRATEGIA 1: Extracción directa de texto (PDFs digitales) ────────────
    # Funciona con cualquier PDF que tenga texto embebido, sin necesitar Poppler
    if is_pdf:
        # Intento 1a: pdfplumber (excelente para PDFs con estructura)
        try:
            import pdfplumber
            from io import BytesIO as _BytesIO
            with pdfplumber.open(_BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if t:
                        pages_text.append(t)
                texto_extraido = "\n--- PÁGINA ---\n".join(pages_text)
            print(f"[ExtraccionTexto] pdfplumber: {len(texto_extraido)} caracteres extraídos")
        except Exception as e_plumber:
            errores_extraccion.append(f"pdfplumber: {e_plumber}")
            print(f"[ExtraccionTexto] pdfplumber falló: {e_plumber}")

        # Intento 1b: PyMuPDF/fitz si pdfplumber no extrajo suficiente texto
        if len(texto_extraido.strip()) < 100:
            try:
                import fitz  # PyMuPDF
                from io import BytesIO as _BytesIO2
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                pages_text = []
                for page in doc:
                    pages_text.append(page.get_text())
                doc.close()
                texto_fitz = "\n--- PÁGINA ---\n".join(pages_text)
                if len(texto_fitz.strip()) > len(texto_extraido.strip()):
                    texto_extraido = texto_fitz
                print(f"[ExtraccionTexto] PyMuPDF: {len(texto_extraido)} caracteres extraídos")
            except Exception as e_fitz:
                errores_extraccion.append(f"PyMuPDF: {e_fitz}")
                print(f"[ExtraccionTexto] PyMuPDF falló: {e_fitz}")

    # ── NORMALIZACIÓN DE ENCODING ─────────────────────────────────────────────
    # Los PDFs bolivianos suelen usar latin-1 internamente. Corregimos caracteres
    # corruptos (Ñ, tildes, etc.) que se muestran como '\ufffd' o '?'.
    if texto_extraido:
        try:
            # Intentar decodificar como latin-1 si hay caracteres de reemplazo
            if '\ufffd' in texto_extraido or '?' in texto_extraido:
                # Re-encodear en latin-1 y decodificar en utf-8 para reparar mojibake
                texto_reparado = texto_extraido.encode('latin-1', errors='replace').decode('utf-8', errors='replace')
                # Solo usar si tiene más caracteres legibles que el original
                if texto_reparado.count('\ufffd') < texto_extraido.count('\ufffd'):
                    texto_extraido = texto_reparado
        except Exception:
            pass  # Mantener el texto original si la reparación falla

    # ── ESTRATEGIA 2: OCR con Tesseract (PDFs escaneados / imágenes) ──────────
    # Solo si las estrategias anteriores no extrajeron suficiente texto
    if len(texto_extraido.strip()) < 100:
        print("[ExtraccionTexto] Texto insuficiente, intentando OCR con Tesseract...")
        try:
            import pytesseract
            from PIL import Image
            from pdf2image import convert_from_bytes

            TESSERACT_POSSIBLE_PATHS = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\PERSONAL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
            ]
            for path in TESSERACT_POSSIBLE_PATHS:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

            poppler_path = os.getenv('POPPLER_PATH', None)
            if not poppler_path:
                for p in [r"C:\Program Files\poppler\bin", r"C:\poppler\bin"]:
                    if os.path.exists(p):
                        poppler_path = p
                        break

            if is_pdf:
                images = convert_from_bytes(file_bytes, poppler_path=poppler_path)
                ocr_pages = []
                for img in images:
                    page_text = pytesseract.image_to_string(img, lang='spa')
                    ocr_pages.append(page_text)
                texto_ocr = "\n--- PÁGINA ---\n".join(ocr_pages)
            else:
                img = Image.open(BytesIO(file_bytes))
                texto_ocr = pytesseract.image_to_string(img, lang='spa')

            if len(texto_ocr.strip()) > len(texto_extraido.strip()):
                texto_extraido = texto_ocr
            print(f"[ExtraccionTexto] Tesseract OCR: {len(texto_extraido)} caracteres extraídos")

        except Exception as exc_ocr:
            errores_extraccion.append(f"Tesseract OCR: {exc_ocr}")
            print(f"[ExtraccionTexto] OCR Tesseract también falló: {exc_ocr}")

    # ── FALLO TOTAL: No se pudo extraer texto por ningún método ───────────────
    if len(texto_extraido.strip()) < 50:
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.ERROR
        verificacion.resumen_publico = (
            "No se pudo extraer texto del documento. "
            "Asegúrese de que el PDF no esté protegido con contraseña y que sea legible. "
            "Si es un documento escaneado, capture una imagen JPG o PNG con buena iluminación."
        )
        detalle_errores = " | ".join(errores_extraccion) if errores_extraccion else "Sin detalles"
        verificacion.texto_ocr = f"[SIN TEXTO]: Solo se extrajeron {len(texto_extraido.strip())} caracteres. Errores: {detalle_errores}"
        verificacion.save()
        return verificacion

    verificacion.texto_ocr = texto_extraido.strip()
    verificacion.save()


    # 3. Analizar con Groq
    api_key = settings.GROQ_API_KEY
    if not api_key:
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.ERROR
        verificacion.resumen_publico = "Error: API Key de Groq no configurada"
        verificacion.save()
        return verificacion

    # Determinar el propietario esperado para comparar
    propietario_nombre = inmueble.propietario.get_full_name() if inmueble.propietario else 'Desconocido'
    propietario_ci = getattr(inmueble.propietario, 'ci', '') if inmueble.propietario else ''

    prompt = f"""
Eres un Abogado Registral Boliviano altamente especializado en la verificación de documentos de Derechos Reales.
Tu misión es determinar si el texto proporcionado corresponde REALMENTE a un documento de título de propiedad inmobiliaria boliviano (Folio Real, Escritura Pública, Minuta de Transferencia, Testimonio de DDRR).

--- INICIO DEL TEXTO EXTRAÍDO DEL DOCUMENTO ---
{texto_extraido}
--- FIN DEL TEXTO DEL DOCUMENTO ---

Datos esperados del propietario del inmueble (para validar si coincide el documento):
- Nombre del propietario registrado: {propietario_nombre}
- CI del propietario: {propietario_ci if propietario_ci else 'No disponible'}

SIGUE ESTAS REGLAS ESTRICTAMENTE:

**REGLA CRÍTICA #1 - VERIFICAR QUE ES UN TÍTULO:**
Antes de analizar cualquier dato, determina si el texto contiene elementos propios de un título de propiedad boliviano:
- Términos como: "Folio Real", "Derechos Reales", "DDRR", "Matrícula", "Escritura Pública", "Testimonio", "Asiento", "Gravamen", "Hipoteca", "Propietario registrado", "Superficie", "Municipio", etc.
- Si el documento parece ser un CV/currículum, factura, contrato laboral, certificado académico, recibo, carta, o cualquier otro tipo de documento que NO sea un título de propiedad inmobiliaria:
  * Asigna "estado": "rechazado"
  * Asigna "tipo_documento": "Desconocido"
  * Asigna "score_confianza": 0
  * En "resumen_publico" explica claramente que el documento no corresponde a un título de propiedad.
  * Deja los demás campos como null o listas vacías.
  * NO inventes datos registrales.

**REGLA #2 - VERIFICAR PROPIETARIO:**
Si el documento sí es un título de propiedad, verifica que el nombre del propietario encontrado en el documento coincida razonablemente con el propietario esperado: "{propietario_nombre}".
Si el propietario NO coincide, asigna "estado": "rechazado" y añade una alerta explicando la discrepancia.

**REGLA #3 - VERIFICAR GRAVÁMENES:**
Si hay hipotecas, embargos, anotaciones preventivas o deudas activas, asigna "estado": "observado" o "rechazado" según la gravedad.

El JSON de respuesta debe tener EXACTAMENTE esta estructura:
{{
  "tipo_documento": "Folio Real" | "Escritura Pública" | "Minuta de Transferencia" | "Desconocido",
  "propietario_registrado": "Nombre completo del propietario encontrado en el documento, o null",
  "documento_identidad": "CI del propietario (ej. 1234567 LP), o null",
  "matricula_inmobiliaria": "Número de matrícula / Folio Real (ej. 7.01.1.01.XXXX), o null",
  "superficie_registrada_m2": número o null,
  "departamento": "ej. La Paz" o null,
  "municipio": "ej. Santa Cruz de la Sierra" o null,
  "zona": "ej. Equipetrol" o null,
  "gravamenes": ["lista de gravámenes detectados, vacío si ninguno"],
  "alertas": ["lista de alertas o irregularidades detectadas"],
  "score_confianza": número entre 0 y 100,
  "estado": "verificado" | "observado" | "rechazado",
  "resumen_publico": "Resumen ejecutivo claro del resultado del análisis."
}}

Retorna ÚNICAMENTE el objeto JSON crudo. Sin comentarios, sin explicaciones, sin bloques ```json```.
"""

    headers_req = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Eres un Abogado Registral Boliviano experto. Analizas títulos de propiedad y retornas un objeto JSON estructurado con la evaluación legal."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 1500
    }

    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers_req, timeout=60)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content'].strip()
        
        # Limpiar markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        resultado_json = json.loads(content)
    except Exception as e_groq:
        err_msg = str(e_groq)
        if hasattr(e_groq, 'response') and e_groq.response is not None:
            try:
                err_msg = f"{e_groq.response.status_code} - {e_groq.response.text}"
            except Exception:
                pass
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.ERROR
        verificacion.resumen_publico = f"Error al analizar el título con la IA de Groq: {err_msg}"
        verificacion.texto_ocr = f"[ERROR GROQ IA]: {err_msg}"
        verificacion.save()
        raise Exception(f"Error al analizar el título con la IA de Groq: {err_msg}")

    # 4. Procesar y guardar la respuesta de la IA en la base de datos
    estado_ia = str(resultado_json.get('estado', 'rechazado')).lower().strip()
    if estado_ia == 'verificado':
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.VERIFICADO
    elif estado_ia == 'observado':
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.OBSERVADO
    elif estado_ia == 'rechazado':
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.RECHAZADO
    else:
        verificacion.estado = VerificacionTitulo.EstadoVerificacion.RECHAZADO

    verificacion.resultado_ia = resultado_json
    verificacion.score_confianza = resultado_json.get('score_confianza', 0)
    verificacion.resumen_publico = resultado_json.get('resumen_publico', 'Resultado del análisis registral.')
    verificacion.save()

    # Crear notificación al propietario
    crear_notificacion_sistema(
        usuario=inmueble.propietario,
        titulo='Verificación de Título Procesada',
        mensaje=f'El análisis legal del título para "{inmueble.titulo}" ha finalizado. Estado: {verificacion.get_estado_display()}. Confianza: {verificacion.score_confianza}%.',
        tipo=Notificacion.TipoNotificacion.CONFIRMACION if verificacion.estado == VerificacionTitulo.EstadoVerificacion.VERIFICADO else Notificacion.TipoNotificacion.ALERTA
    )

    return verificacion


def crear_contrato_con_ia(propietario, datos: dict, historial_chat: list):
    """Crea un contrato usando la IA para enriquecer las cláusulas a partir
    del historial de chat del propietario con el Asistente Legal.

    Args:
        propietario: Usuario propietario que crea el contrato
        datos: Dict con campos básicos: inmueble_id, inquilino_id, chat_id,
               tipo_contrato_id, monto, moneda, inicio, fin, deposito, dia_pago
        historial_chat: Lista [{role, content}] de la conversación con la IA

    Returns:
        Contrato: El contrato creado y enviado al cliente
    """
    from .models import Contrato, TipoContrato, Inmueble
    from usuarios.models import Chat, Mensaje, Notificacion
    from usuarios.services import crear_notificacion_sistema
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 1. Valores por defecto iniciales provistos por el formulario
    monto_val = datos['monto']
    deposito_val = datos.get('deposito', '0')
    try:
        dia_pago_val = int(datos.get('dia_pago', 1))
    except (ValueError, TypeError):
        dia_pago_val = 1

    clausulas_ia = datos.get('clausulas', '')
    restricciones_ia = datos.get('restricciones', '')
    penalidades_ia = datos.get('penalidades', '')
    condiciones_uso_ia = datos.get('condiciones_uso', '')
    incluye_servicios_ia = datos.get('incluye_servicios', '')

    if historial_chat and len(historial_chat) > 1:
        api_key = settings.GROQ_API_KEY
        if api_key:
            conversacion_texto = '\n'.join(
                f"{'Propietario' if m['role'] == 'user' else 'Abogado IA'}: {m['content']}"
                for m in historial_chat
                if m.get('content', '').strip()
            )
            prompt_extraccion = f"""Eres un asistente legal boliviano. A continuación hay una conversación entre un propietario y un asistente legal sobre las condiciones de un contrato inmobiliario.

Monto de alquiler base: {datos.get('monto')} {datos.get('moneda', 'BOB')}

CONVERSACIÓN:
{conversacion_texto}

TAREA: Extrae y sintetiza las condiciones específicas que el propietario quiere en el contrato.
Devuelve un JSON con exactamente estas claves (solo el JSON puro, sin bloques de código ni markdown):
{{
  "clausulas": "Cláusulas principales mencionadas o acordadas",
  "restricciones": "Restricciones específicas del propietario",
  "penalidades": "Penalidades acordadas",
  "condiciones_uso": "Condiciones de uso del inmueble",
  "incluye_servicios": "Servicios incluidos o excluidos",
  "monto": "Monto de alquiler mensual numérico (solo dígitos) si se acordó/cambió en el chat (sino null)",
  "deposito": "Monto de garantía/depósito numérico (solo dígitos) si se acordó/cambió en el chat. Ej. si se acordaron 2 meses de garantía, calcula 2 * monto base (sino null)",
  "dia_pago": "Día del mes para pago (número entre 1 y 31) si se acordó/cambió en el chat (sino null)"
}}
Responde SOLO el JSON."""

            try:
                headers_req = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "Eres un asistente legal boliviano. Extrae condiciones contractuales de conversaciones y responde solo con JSON puro."},
                        {"role": "user", "content": prompt_extraccion}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024
                }
                resp = requests.post(GROQ_API_URL, json=payload, headers=headers_req, timeout=30)
                resp.raise_for_status()
                content = resp.json()['choices'][0]['message']['content'].strip()
                # Limpiar markdown residual
                for prefix in ["```json", "```"]:
                    if content.startswith(prefix):
                        content = content[len(prefix):]
                if content.endswith("```"):
                    content = content[:-3]
                extraido = json.loads(content.strip())
                
                if extraido.get('clausulas'):
                    clausulas_ia = extraido['clausulas']
                if extraido.get('restricciones'):
                    restricciones_ia = extraido['restricciones']
                if extraido.get('penalidades'):
                    penalidades_ia = extraido['penalidades']
                if extraido.get('condiciones_uso'):
                    condiciones_uso_ia = extraido['condiciones_uso']
                if extraido.get('incluye_servicios'):
                    incluye_servicios_ia = extraido['incluye_servicios']

                # Extraer monto, depósito/garantía y día de pago de la memoria/chat
                if extraido.get('monto'):
                    try:
                        monto_val = str(int(float(extraido['monto'])))
                    except (ValueError, TypeError):
                        pass
                if extraido.get('deposito'):
                    try:
                        deposito_val = str(int(float(extraido['deposito'])))
                    except (ValueError, TypeError):
                        pass
                if extraido.get('dia_pago'):
                    try:
                        dia_pago_val = int(extraido['dia_pago'])
                    except (ValueError, TypeError):
                        pass
            except Exception as e:
                print(f"[crear_contrato_con_ia] Error extrayendo datos con IA: {e}")

    # 2. Obtener objetos relacionados
    inmueble = Inmueble.objects.get(id=datos['inmueble_id'])
    inquilino = User.objects.get(id=datos['inquilino_id'])
    tipo_contrato = TipoContrato.objects.get(id=datos['tipo_contrato_id'])
    chat_obj = None
    if datos.get('chat_id'):
        try:
            chat_obj = Chat.objects.get(id=datos['chat_id'])
        except Chat.DoesNotExist:
            pass

    # 3. Crear el contrato en base de datos
    with transaction.atomic():
        contrato = Contrato.objects.create(
            inmueble=inmueble,
            inquilino=inquilino,
            chat=chat_obj,
            tipo_contrato=tipo_contrato,
            monto=monto_val,
            moneda=datos.get('moneda', 'BOB'),
            inicio=datos['inicio'],
            fin=datos.get('fin') or None,
            deposito=deposito_val,
            dia_pago=dia_pago_val,
            clausulas=clausulas_ia,
            restricciones=restricciones_ia,
            penalidades=penalidades_ia,
            condiciones_uso=condiciones_uso_ia,
            incluye_servicios=incluye_servicios_ia,
            estado='enviado',
        )

        # 4. Enviar mensaje CONTRATO_REVIEW al chat
        if chat_obj:
            Mensaje.objects.create(
                chat=chat_obj,
                remitente=propietario,
                tipo='texto',
                contenido=(
                    f'📋 CONTRATO ENVIADO\n'
                    f'Propiedad: {inmueble.titulo}\n'
                    f'Tipo: {tipo_contrato.nombre}\n'
                    f'Monto: ${contrato.monto} {contrato.moneda}\n'
                    f'Período: {contrato.inicio} → {contrato.fin or "Indefinido"}\n'
                    f'───────────────\n'
                    f'CONTRATO_REVIEW:{contrato.id}:END'
                ),
            )
            chat_obj.save()

        # 5. Notificar al inquilino
        crear_notificacion_sistema(
            usuario=inquilino,
            titulo='Nuevo contrato para revisar',
            mensaje=f'{propietario.get_full_name()} te ha enviado un contrato para "{inmueble.titulo}". Revísalo en el chat.',
            tipo=Notificacion.TipoNotificacion.INFO,
        )

    return contrato


def editar_contrato_con_ia(contrato, propietario, datos: dict, historial_chat: list):
    """Actualiza un contrato existente enriqueciendo las cláusulas con la IA
    y guardando los campos actualizados.

    Args:
        contrato: Instancia de Contrato a editar
        propietario: Usuario propietario
        datos: Dict con campos a actualizar: tipo_contrato_id, monto, moneda, inicio, fin, deposito, dia_pago
        historial_chat: Lista [{role, content}]
    """
    from .models import TipoContrato
    from usuarios.models import Mensaje
    from django.conf import settings
    from django.db import transaction
    import requests
    import json

    # 1. Valores base
    monto_val = datos.get('monto', contrato.monto)
    deposito_val = datos.get('deposito', contrato.deposito)
    try:
        dia_pago_val = int(datos.get('dia_pago', contrato.dia_pago))
    except (ValueError, TypeError):
        dia_pago_val = contrato.dia_pago

    clausulas_ia = contrato.clausulas
    restricciones_ia = contrato.restricciones
    penalidades_ia = contrato.penalidades
    condiciones_uso_ia = contrato.condiciones_uso
    incluye_servicios_ia = contrato.incluye_servicios

    # Extraer si hay historial
    if historial_chat and len(historial_chat) > 1:
        api_key = settings.GROQ_API_KEY
        if api_key:
            conversacion_texto = '\n'.join(
                f"{'Propietario' if m['role'] == 'user' else 'Abogado IA'}: {m['content']}"
                for m in historial_chat
                if m.get('content', '').strip()
            )
            prompt_extraccion = f"""Eres un asistente legal boliviano. A continuación hay una conversación entre un propietario y un asistente legal sobre las condiciones de un contrato inmobiliario.

Monto de alquiler base: {monto_val} {datos.get('moneda', contrato.moneda)}

CONVERSACIÓN:
{conversacion_texto}

TAREA: Extrae y sintetiza las condiciones específicas que el propietario quiere en el contrato.
Devuelve un JSON con exactamente estas claves (solo el JSON puro, sin bloques de código ni markdown):
{{
  "clausulas": "Cláusulas principales mencionadas o acordadas",
  "restricciones": "Restricciones específicas del propietario",
  "penalidades": "Penalidades acordadas",
  "condiciones_uso": "Condiciones de uso del inmueble",
  "incluye_servicios": "Servicios incluidos o excluidos",
  "monto": "Monto de alquiler mensual numérico (solo dígitos) si se acordó/cambió en el chat (sino null)",
  "deposito": "Monto de garantía/depósito numérico (solo dígitos) si se acordó/cambió en el chat. Ej. si se acordaron 2 meses de garantía, calcula 2 * monto base (sino null)",
  "dia_pago": "Día del mes para pago (número entre 1 y 31) si se acordó/cambió en el chat (sino null)"
}}
Responde SOLO el JSON."""

            try:
                headers_req = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "Eres un asistente legal boliviano. Extrae condiciones contractuales de conversaciones y responde solo con JSON puro."},
                        {"role": "user", "content": prompt_extraccion}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024
                }
                resp = requests.post(GROQ_API_URL, json=payload, headers=headers_req, timeout=30)
                resp.raise_for_status()
                content = resp.json()['choices'][0]['message']['content'].strip()
                for prefix in ["```json", "```"]:
                    if content.startswith(prefix):
                        content = content[len(prefix):]
                if content.endswith("```"):
                    content = content[:-3]
                extraido = json.loads(content.strip())

                if extraido.get('clausulas'):
                    clausulas_ia = extraido['clausulas']
                if extraido.get('restricciones'):
                    restricciones_ia = extraido['restricciones']
                if extraido.get('penalidades'):
                    penalidades_ia = extraido['penalidades']
                if extraido.get('condiciones_uso'):
                    condiciones_uso_ia = extraido['condiciones_uso']
                if extraido.get('incluye_servicios'):
                    incluye_servicios_ia = extraido['incluye_servicios']

                # Extraer numéricos
                if extraido.get('monto'):
                    try:
                        monto_val = str(int(float(extraido['monto'])))
                    except (ValueError, TypeError):
                        pass
                if extraido.get('deposito'):
                    try:
                        deposito_val = str(int(float(extraido['deposito'])))
                    except (ValueError, TypeError):
                        pass
                if extraido.get('dia_pago'):
                    try:
                        dia_pago_val = int(extraido['dia_pago'])
                    except (ValueError, TypeError):
                        pass
            except Exception as e:
                print(f"[editar_contrato_con_ia] Error extrayendo con IA: {e}")

    # 2. Actualizar campos
    tipo_contrato = TipoContrato.objects.get(id=datos['tipo_contrato_id']) if datos.get('tipo_contrato_id') else contrato.tipo_contrato
    
    with transaction.atomic():
        contrato.tipo_contrato = tipo_contrato
        contrato.monto = monto_val
        contrato.moneda = datos.get('moneda', contrato.moneda)
        contrato.inicio = datos.get('inicio', contrato.inicio)
        contrato.fin = datos.get('fin') or None
        contrato.deposito = deposito_val
        contrato.dia_pago = dia_pago_val
        contrato.clausulas = clausulas_ia
        contrato.restricciones = restricciones_ia
        contrato.penalidades = penalidades_ia
        contrato.condiciones_uso = condiciones_uso_ia
        contrato.incluye_servicios = incluye_servicios_ia
        # Si fue rechazado, vuelve a 'enviado' para revisión
        if contrato.estado == 'rechazado':
            contrato.estado = 'enviado'
            contrato.motivo_rechazo = ''
        contrato.save()

        # Enviar mensaje de actualización al chat
        if contrato.chat:
            Mensaje.objects.create(
                chat=contrato.chat,
                remitente=propietario,
                tipo='texto',
                contenido=(
                    f'📋 CONTRATO ACTUALIZADO\n'
                    f'Propiedad: {contrato.inmueble.titulo}\n'
                    f'Tipo: {tipo_contrato.nombre}\n'
                    f'Monto: ${contrato.monto} {contrato.moneda}\n'
                    f'Período: {contrato.inicio} → {contrato.fin or "Indefinido"}\n'
                    f'───────────────\n'
                    f'CONTRATO_REVIEW:{contrato.id}:END'
                ),
            )
            contrato.chat.save()

    return contrato

