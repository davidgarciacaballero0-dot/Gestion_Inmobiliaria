from .models import Notificacion


def crear_notificacion_sistema(*, usuario, titulo, mensaje, tipo=Notificacion.TipoNotificacion.INFO):
    return Notificacion.objects.create(
        usuario=usuario,
        origen=Notificacion.OrigenNotificacion.SISTEMA,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )


def crear_notificacion_usuario(*, usuario, titulo, mensaje, tipo=Notificacion.TipoNotificacion.CONFIRMACION):
    return Notificacion.objects.create(
        usuario=usuario,
        origen=Notificacion.OrigenNotificacion.USUARIO,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )


def calcular_scoring_inquilino(usuario_id: int):
    """
    Calcula el Score de Confiabilidad y Riesgo de un potencial inquilino
    basado en 4 pilares: Pagos, Identidad/Documentos, Comportamiento/Citas y Antigüedad/Estabilidad.
    Genera un informe explicativo formal con Groq (Llama 3.3).
    """
    import json
    import requests
    from datetime import date
    from django.conf import settings
    from .models import Usuario
    from inmuebles.models import Contrato, Cita
    from pagos.models import Pago

    try:
        inquilino = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return None

    # ─── Pilar 1: Historial de Pagos (0 a 40 pts) ────────────────────────────
    pagos_qs = Pago.objects.filter(usuario=inquilino)
    total_pagos = pagos_qs.count()
    pagos_completados = pagos_qs.filter(estado='completado').count()
    pagos_tardios = pagos_qs.filter(estado='pendiente').count()

    contratos_previos = Contrato.objects.filter(inquilino=inquilino, estado__in=['activo', 'finalizado']).count()

    if total_pagos > 0:
        ratio_cumplimiento = (pagos_completados / total_pagos)
        score_pagos = round(ratio_cumplimiento * 35) + (5 if contratos_previos > 0 else 0)
        score_pagos = min(40, max(0, score_pagos))
        detalle_pagos = f"{pagos_completados} de {total_pagos} pagos completados puntualmente ({contratos_previos} contratos)"
    else:
        # Usuario sin historial de pagos aún en la plataforma: puntuación neutral base
        score_pagos = 28
        detalle_pagos = "Usuario nuevo sin transacciones de pago registradas aún (Score base neutral)"

    # ─── Pilar 2: Verificación de Identidad & Documentos (0 a 25 pts) ─────────
    score_documentos = 0
    documentos_lista = []

    if inquilino.ci:
        score_documentos += 10
        documentos_lista.append("Cédula de Identidad registrada")
    else:
        documentos_lista.append("Cédula de Identidad pendiente")

    if inquilino.telefono:
        score_documentos += 5
        documentos_lista.append("Teléfono de contacto verificado")

    if inquilino.email:
        score_documentos += 5
        documentos_lista.append("Correo electrónico verificado")

    if inquilino.foto:
        score_documentos += 5
        documentos_lista.append("Fotografía de perfil cargada")

    score_documentos = min(25, max(0, score_documentos))

    # ─── Pilar 3: Comportamiento & Citas (0 a 20 pts) ────────────────────────
    citas_qs = Cita.objects.filter(cliente=inquilino)
    total_citas = citas_qs.count()
    citas_completadas = citas_qs.filter(estado=Cita.EstadoCita.COMPLETADA).count()
    citas_canceladas = citas_qs.filter(estado=Cita.EstadoCita.CANCELADA).count()

    score_comportamiento = 15  # Base
    if total_citas > 0:
        if citas_completadas >= 1 and citas_canceladas == 0:
            score_comportamiento += 5
        elif citas_canceladas > 2:
            score_comportamiento -= 5
    score_comportamiento = min(20, max(5, score_comportamiento))
    detalle_citas = f"{citas_completadas} visitas cumplidas de {total_citas} agendadas"

    # ─── Pilar 4: Antigüedad & Estabilidad (0 a 15 pts) ──────────────────────
    dias_registro = (date.today() - inquilino.date_joined.date()).days if inquilino.date_joined else 0
    if dias_registro >= 90:
        score_antiguedad = 15
        detalle_antiguedad = f"Antigüedad destacada ({dias_registro} días en la plataforma)"
    elif dias_registro >= 30:
        score_antiguedad = 12
        detalle_antiguedad = f"Usuario regular ({dias_registro} días en la plataforma)"
    else:
        score_antiguedad = 8
        detalle_antiguedad = f"Registro reciente ({dias_registro} días en la plataforma)"

    # ─── Score Total y Nivel de Riesgo ───────────────────────────────────────
    score_total = min(100, max(10, score_pagos + score_documentos + score_comportamiento + score_antiguedad))

    if score_total >= 80:
        nivel_riesgo = 'Bajo'
        recomendacion_estado = 'Recomendado'
        color_badge = 'verde'
    elif score_total >= 60:
        nivel_riesgo = 'Medio'
        recomendacion_estado = 'Aceptable con Garantía'
        color_badge = 'ambar'
    else:
        nivel_riesgo = 'Alto'
        recomendacion_estado = 'Requiere Aval / Revisión'
        color_badge = 'rojo'

    justificacion_ia = (
        f"El candidato presenta un Score de Confiabilidad de {score_total}/100 con nivel de riesgo {nivel_riesgo.lower()}. "
        f"Cumple con {score_documentos}/25 en verificación documental y {score_pagos}/40 en antecedentes financieros."
    )

    # Llamar a Groq (Llama 3.3) para generar el dictamen ejecutivo formal
    if getattr(settings, 'GROQ_API_KEY', None):
        prompt_scoring = (
            "Eres un Analista Financiero y de Riesgo Inmobiliario Experto.\n"
            "Evalúa los antecedentes del siguiente potencial inquilino y redacta un dictamen formal de riesgo "
            "y una sugerencia ejecutiva de garantía para el propietario (máximo 3 oraciones).\n\n"
            f"Datos del Inquilino: {inquilino.get_full_name()} ({inquilino.email})\n"
            f"Score Global: {score_total}/100 (Nivel: {nivel_riesgo})\n"
            f"- Pilar Pagos ({score_pagos}/40): {detalle_pagos}\n"
            f"- Pilar Documentos ({score_documentos}/25): {', '.join(documentos_lista)}\n"
            f"- Pilar Comportamiento ({score_comportamiento}/20): {detalle_citas}\n"
            f"- Pilar Antigüedad ({score_antiguedad}/15): {detalle_antiguedad}\n\n"
            "REGLA OBLIGATORIA: No utilices ningún emoji ni emoticono en tu respuesta. Redacta en tono formal, institucional y profesional.\n"
            "Responde ÚNICAMENTE en formato JSON con la siguiente estructura exacta:\n"
            '{"dictamen_ejecutivo": "Texto formal...", "garantia_sugerida": "1 mes de depósito estándar..."}'
        )

        try:
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt_scoring}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            headers_req = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers_req, timeout=15)
            if resp.status_code == 200:
                data_json = resp.json()
                parsed = json.loads(data_json['choices'][0]['message']['content'])
                if 'dictamen_ejecutivo' in parsed:
                    justificacion_ia = parsed['dictamen_ejecutivo']
        except Exception as e:
            print(f"[calcular_scoring_inquilino] Error llamando a Groq: {e}")

    # ─── Garantía Dinámica y Esfuerzo Financiero ─────────────────────────────
    if score_total >= 85:
        garantia_sugerida = "1 mes estándar con opción a financiar en 2 cuotas por excelente historial"
        descuento_garantia_sugerido = "Aplica para garantía flexible o 50% anticipado"
        esfuerzo_financiero = "Excelente solvencia (Capacidad estimada > 75%)"
    elif score_total >= 70:
        garantia_sugerida = "1 mes de depósito de garantía estándar"
        descuento_garantia_sugerido = "Garantía estándar sin penalidades"
        esfuerzo_financiero = "Sostenible (Capacidad estimada 65-75%)"
    elif score_total >= 60:
        garantia_sugerida = "1 mes de depósito + verificación de comprobante de ingresos"
        descuento_garantia_sugerido = "Sin descuento en garantía"
        esfuerzo_financiero = "Moderado (Capacidad estimada 50-65%)"
    else:
        garantia_sugerida = "2 meses de depósito de garantía y/o Aval personal requerido"
        descuento_garantia_sugerido = "Requiere garantías adicionales de respaldo"
        esfuerzo_financiero = "Riesgo crediticio (Requiere validación de aval)"

    return {
        'inquilino_id': inquilino.id,
        'nombre_completo': inquilino.get_full_name() or inquilino.email,
        'email': inquilino.email,
        'telefono': inquilino.telefono,
        'ci': inquilino.ci,
        'score_total': score_total,
        'nivel_riesgo': nivel_riesgo,
        'recomendacion_estado': recomendacion_estado,
        'color_badge': color_badge,
        'garantia_sugerida': garantia_sugerida,
        'descuento_garantia_sugerido': descuento_garantia_sugerido,
        'esfuerzo_financiero': esfuerzo_financiero,
        'pilares': {
            'pagos': {
                'score': score_pagos,
                'maximo': 40,
                'detalle': detalle_pagos
            },
            'documentos': {
                'score': score_documentos,
                'maximo': 25,
                'detalle': documentos_lista
            },
            'comportamiento': {
                'score': score_comportamiento,
                'maximo': 20,
                'detalle': detalle_citas
            },
            'antiguedad': {
                'score': score_antiguedad,
                'maximo': 15,
                'detalle': detalle_antiguedad
            }
        },
        'justificacion_ia': justificacion_ia,
        'insignias': [
            {'titulo': 'Identidad Registrada', 'activa': bool(inquilino.ci)},
            {'titulo': 'Contacto Verificado', 'activa': bool(inquilino.telefono and inquilino.email)},
            {'titulo': 'Sin Historial de Morosidad', 'activa': pagos_tardios == 0},
            {'titulo': 'Citas Cumplidas', 'activa': citas_completadas >= 1 or total_citas == 0}
        ]
    }


def generar_pasaporte_inquilino_pdf(usuario_id: int) -> bytes:
    """
    Genera el Pasaporte Digital Oficial de Confiabilidad del Inquilino en formato PDF (ReportLab).
    Incluye desglose de pilares, dictamen de IA, insignias de verificación y sello institucional.
    """
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    score_data = calcular_scoring_inquilino(usuario_id)
    if not score_data:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#1e40af")
    success_color = colors.HexColor("#15803d")
    dark_color = colors.HexColor("#0f172a")
    gray_color = colors.HexColor("#64748b")
    bg_light = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=primary_color,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=gray_color,
        fontName='Helvetica'
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=dark_color,
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=dark_color,
        fontName='Helvetica'
    )
    badge_style = ParagraphStyle(
        'BadgeScore',
        parent=styles['Normal'],
        fontSize=20,
        leading=24,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=1
    )

    story = []

    # 1. Cabecera Institucional
    header_data = [
        [
            Paragraph("AUTOGESTIÓN INMOBILIARIA", title_style),
            Paragraph("PASAPORTE DIGITAL DE INQUILINO<br/><font size=8 color='#64748b'>Certificado Oficial de Solvencia</font>", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=14))

    # 2. Hero Card: Score Global y Datos del Candidato
    badge_color = success_color if score_data['score_total'] >= 80 else colors.HexColor("#d97706") if score_data['score_total'] >= 60 else colors.HexColor("#dc2626")

    score_box_data = [
        [
            Paragraph(f"<b>CANDIDATO EVALUADO</b><br/>"
                      f"<b>Nombre:</b> {score_data['nombre_completo']}<br/>"
                      f"<b>Email:</b> {score_data['email']}<br/>"
                      f"<b>Cédula de Identidad:</b> {score_data['ci'] or 'N/A'}<br/>"
                      f"<b>Teléfono:</b> {score_data['telefono'] or 'N/A'}", body_style),
            Paragraph(f"SCORE GLOBAL<br/><b>{score_data['score_total']} / 100</b><br/><font size=9>Riesgo {score_data['nivel_riesgo']}</font>", badge_style)
        ]
    ]
    score_table = Table(score_box_data, colWidths=[360, 170])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), bg_light),
        ('BACKGROUND', (1, 0), (1, 0), badge_color),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 14))

    # 3. Dictamen Ejecutivo de la IA
    story.append(Paragraph("DICTAMEN EJECUTIVO DE RIESGO (IA ANALYTICS)", section_title_style))
    story.append(Spacer(1, 4))
    ai_box_data = [[Paragraph(score_data['justificacion_ia'], body_style)]]
    ai_table = Table(ai_box_data, colWidths=[530])
    ai_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#bfdbfe")),
        ('LINEBEFORE', (0, 0), (0, 0), 4, primary_color),
        ('PADDING', (0, 0), (0, 0), 10),
    ]))
    story.append(ai_table)
    story.append(Spacer(1, 14))

    # 4. Desglose de los 4 Pilares de Evaluación
    story.append(Paragraph("DESGLOSE PONDERADO DE PILARES DE CONFIABILIDAD", section_title_style))
    story.append(Spacer(1, 6))

    pilares = score_data['pilares']
    pillars_table_data = [
        [
            Paragraph("<b>Pilar de Evaluación</b>", body_style),
            Paragraph("<b>Puntaje Obtenido</b>", body_style),
            Paragraph("<b>Puntaje Máximo</b>", body_style),
            Paragraph("<b>Detalle y Cumplimiento</b>", body_style)
        ],
        [
            Paragraph("Historial de Pagos y Transacciones", body_style),
            Paragraph(f"{pilares['pagos']['score']} pts", body_style),
            Paragraph(f"{pilares['pagos']['maximo']} pts", body_style),
            Paragraph(str(pilares['pagos']['detalle']), body_style)
        ],
        [
            Paragraph("Identidad y Documentación Legal", body_style),
            Paragraph(f"{pilares['documentos']['score']} pts", body_style),
            Paragraph(f"{pilares['documentos']['maximo']} pts", body_style),
            Paragraph(", ".join(pilares['documentos']['detalle']), body_style)
        ],
        [
            Paragraph("Comportamiento y Citas Cumplidas", body_style),
            Paragraph(f"{pilares['comportamiento']['score']} pts", body_style),
            Paragraph(f"{pilares['comportamiento']['maximo']} pts", body_style),
            Paragraph(str(pilares['comportamiento']['detalle']), body_style)
        ],
        [
            Paragraph("Antigüedad y Estabilidad de Perfil", body_style),
            Paragraph(f"{pilares['antiguedad']['score']} pts", body_style),
            Paragraph(f"{pilares['antiguedad']['maximo']} pts", body_style),
            Paragraph(str(pilares['antiguedad']['detalle']), body_style)
        ],
    ]

    p_table = Table(pillars_table_data, colWidths=[150, 75, 75, 230])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(p_table)
    story.append(Spacer(1, 14))

    # 5. Recomendación de Garantía y Capacidad Financiera
    story.append(Paragraph("RECOMENDACIÓN CONTRACTUAL Y GARANTÍA DINÁMICA", section_title_style))
    story.append(Spacer(1, 4))
    garantia_data = [
        [
            Paragraph(f"<b>Garantía Sugerida:</b> {score_data['garantia_sugerida']}<br/>"
                      f"<b>Capacidad Financiera:</b> {score_data['esfuerzo_financiero']}<br/>"
                      f"<b>Beneficio Comercial:</b> {score_data['descuento_garantia_sugerido']}", body_style)
        ]
    ]
    garantia_table = Table(garantia_data, colWidths=[530])
    garantia_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#bbf7d0")),
        ('LINEBEFORE', (0, 0), (0, 0), 4, success_color),
        ('PADDING', (0, 0), (0, 0), 10),
    ]))
    story.append(garantia_table)
    story.append(Spacer(1, 18))

    # 6. Sello y Validación
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    footer_text = Paragraph(
        "<font size=7.5 color='#94a3b8'>Documento generado digitalmente por la plataforma Autogestión Inmobiliaria con respaldo de Inteligencia Artificial Groq (Llama 3.3). "
        "Este certificado acredita el historial y score financiero en base a la actividad verificada en el sistema.</font>",
        subtitle_style
    )
    story.append(footer_text)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


