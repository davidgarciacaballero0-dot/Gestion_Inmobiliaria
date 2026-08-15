import os
# pyrefly: ignore [missing-import]
import django
from decimal import Decimal
from datetime import date, timedelta, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from usuarios.models import Usuario, Agenda, Notificacion, Chat, Mensaje, Bloqueo, Resena
from inmuebles.models import (
    TipoInmueble, Inmueble, Publicacion, Multimedia, Direccion, TipoContrato, Contrato, Comision,
    Hotspot, Favorito, Cita, HorarioDisponible, VerificacionTitulo, AccesoRecorrido360
)
from pagos.models import (
    TipoPago, Pago, HistorialPago, ConfiguracionSistema, DetallePago, TipoPlan, Plan, TransaccionStripe
)


def create_seed_data():
    print("Creando datos semilla...")

    # Limpiar datos antiguos para evitar duplicados y conflictos de integridad
    print("Limpiando base de datos...")
    Bloqueo.objects.all().delete()
    Resena.objects.all().delete()
    Mensaje.objects.all().delete()
    Chat.objects.all().delete()
    Notificacion.objects.all().delete()
    Agenda.objects.all().delete()
    Comision.objects.all().delete()
    
    AccesoRecorrido360.objects.all().delete()
    Cita.objects.all().delete()
    HorarioDisponible.objects.all().delete()
    VerificacionTitulo.objects.all().delete()
    Favorito.objects.all().delete()
    Hotspot.objects.all().delete()
    
    HistorialPago.objects.all().delete()
    DetallePago.objects.all().delete()
    TransaccionStripe.objects.all().delete()
    Pago.objects.all().delete()
    ConfiguracionSistema.objects.all().delete()
    Contrato.objects.all().delete()
    
    Plan.objects.all().delete()
    TipoPlan.objects.all().delete()
    
    Multimedia.objects.all().delete()
    Publicacion.objects.all().delete()
    Inmueble.objects.all().delete()
    Direccion.objects.all().delete()

    # Inicializar configuración global de comisiones (patrón Singleton)
    config = ConfiguracionSistema.get_config()
    print(f"  OK Configuración de comisiones inicializada en {config.porcentaje_comision_plataforma}%")

    # ═══════════════════════════════════════════════════════════
    #  11 USUARIOS (Admin + 9 + muerte)
    # ═══════════════════════════════════════════════════════════
    if not Usuario.objects.filter(email='admin@autogestion.bo').exists():
        admin = Usuario(
            email='admin@autogestion.bo',
            rol='admin',
            first_name='Carlos',
            last_name='Mendoza',
            ci='9876543',
            telefono='71234567',
            is_staff=True,
            is_superuser=True,
            is_active=True,
    )
        admin.set_password('admin123')
        admin.save()
        print("  OK Superuser: admin@autogestion.bo / admin123")
    else:
        admin = Usuario.objects.get(email='admin@autogestion.bo')

    if not Usuario.objects.filter(email='diego@gmail.com').exists():
        diego = Usuario(
            email='diego@gmail.com',
            rol='admin',
            first_name='Diego',
            last_name='Garcia',
            ci='12948850',
            telefono='78945612',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        diego.set_password('admin123')
        diego.save()
        print("  OK User: diego@gmail.com / admin123")
    else:
        diego = Usuario.objects.get(email='diego@gmail.com')

    usuarios_data = [
        ('propietario1', 'juan.perez@gmail.com', 'Juan', 'Pérez', 'usuario', '1234567', '70011001', date(1985, 3, 15)),
        ('propietario2', 'maria.torres@gmail.com', 'María', 'Torres', 'usuario', '2345678', '70022002', date(1990, 7, 22)),
        ('propietario3', 'roberto.flores@gmail.com', 'Roberto', 'Flores', 'usuario', '3456789', '70033003', date(1988, 1, 10)),
        ('propietario4', 'carla.gutierrez@gmail.com', 'Carla', 'Gutiérrez', 'usuario', '4567890', '70044004', date(1995, 5, 28)),
        ('propietario5', 'diego.quispe@gmail.com', 'Diego', 'Quispe', 'usuario', '5678901', '70055005', date(1992, 11, 3)),
        ('propietario6', 'ana.morales@gmail.com', 'Ana', 'Morales', 'usuario', '6789012', '70066006', date(1993, 9, 12)),
        ('propietario7', 'luis.choque@gmail.com', 'Luis', 'Choque', 'usuario', '7890123', '70077007', date(1991, 4, 8)),
        ('propietario8', 'elena.vargas@gmail.com', 'Elena', 'Vargas', 'usuario', '8901234', '70088008', date(1987, 6, 20)),
        ('propietario9', 'sofia.salazar@gmail.com', 'Sofía', 'Salazar', 'usuario', '9012345', '70099009', date(1994, 2, 14)),
        ('muerte', 'muertemuerte60@gmail.com', 'Muerte', 'Muerte', 'usuario', '78023575', '70100010', date(1990, 1, 1)),
    ]
    
    # users mapea una clave_local del script con el objeto Usuario creado, para relacionar inmuebles/pagos.
    # No representa el atributo 'username' del modelo de base de datos.
    users = {'admin': admin, 'diego': diego}
    for clave_local, email, fn, ln, rol_n, ci, tel, fnac in usuarios_data:
        user, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'first_name': fn, 'last_name': ln,
                'rol': rol_n, 'ci': ci, 'telefono': tel,
                'nacimiento': fnac,
            }
        )
        if created:
            user.set_password('usuario123' if clave_local != 'muerte' else 'muerte60')
            user.save()
        users[clave_local] = user
    print(f"  OK Usuarios creados: {len(users)} (admin + 10)")

    # ═══════════════════════════════════════════════════════════
    #  TIPOS DE INMUEBLE (Categorías)
    # ═══════════════════════════════════════════════════════════
    categorias_data = [
        ('Casa', 'Vivienda unifamiliar independiente.'),
    ]
    tipos = {}
    for nombre, desc in categorias_data:
        tipo, _ = TipoInmueble.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc})
        tipos[nombre] = tipo
    print(f"  OK Categorías: {len(tipos)}")

    # ═══════════════════════════════════════════════════════════
    #  10 INMUEBLES (1-10), uno por cada usuario propietario
    # ═══════════════════════════════════════════════════════════
    inmuebles_data = [
        ('Casa Moderna La Guardia', 'propietario1', 'Casa', 'Casa quinta con terreno amplio en La Guardia.', 'Calle Principal La Guardia', 'La Guardia', 'Zona Centro', 850504, 1239, 2, 2, True, 'disponible'),
        ('Casa en venta Santa Cruz', 'admin', 'Casa', 'Casa grande con amplio terreno.', 'Av. Brasil', 'Santa Cruz', 'Zona Centro', 210560, 384, 4, 1, False, 'disponible'),
        ('Casa Colonial Santa Cruz', 'propietario3', 'Casa', 'Casa en venta con acabados premium.', 'Calle Melchor Pinto', 'Santa Cruz', 'Zona Centro', 146500, 120, 4, 3, True, 'disponible'),
        ('Casa de 2 Pisos', 'admin', 'Casa', 'Casa de 2 pisos con patio.', 'Av. Irala', 'Santa Cruz', 'Zona Centro', 250654, 100, 4, 2, True, 'disponible'),
        ('Casa con Terreno', 'propietario5', 'Casa', 'Terreno y 2 casas. 8.000 m2, piscina, churrasquera, garajes, frutales.', 'Radial 26', 'Santa Cruz', 'Zona Centro', 1563200, 12000, 8, 6, True, 'disponible'),
        ('Casa Equipetrol', 'propietario6', 'Casa', 'Casa grande con excelentes acabados.', 'Av. Equipetrol', 'Santa Cruz', 'Zona Centro', 526300, 6000, 3, 4, True, 'disponible'),
        ('Casa Junín', 'propietario7', 'Casa', 'Casa disponible para venta o alquiler.', 'Calle Junín', 'Santa Cruz', 'Zona Centro', 604540, 450, 3, 2, True, 'disponible'),
        ('Casa Económica', 'propietario8', 'Casa', 'Casa económica: 2 tiendas, 1 Habitación, Baño, Cocina, Sala, Patio amplio, Garage. Documentos en orden.', 'Calle Richardo', 'Santa Cruz', 'Zona Centro', 864050, 374.70, 1, 1, False, 'disponible'),
        ('Casa Potosí', 'propietario9', 'Casa', 'Casa en venta a buen precio.', 'Calle Potosí', 'Santa Cruz', 'Zona Centro', 250600, 2400, 2, 3, True, 'disponible'),
        ('Casa Cambodromo', 'muerte', 'Casa', 'Casa grande en zona residencial.', 'Calle Cambodromo', 'Santa Cruz', 'Zona Centro', 865040, 3000, 6, 3, True, 'disponible'),
        ('Casa zona 2do anillo', 'diego', 'Casa', 'elegante casa entre Av.doble via y 2do anillo', 'Manuela Velasco', 'Santa Cruz', '2do anillo', 100000.00, 11250.00, 5, 5, True, 'disponible'),
    ]
    
    inmuebles = {}
    for idx, (titulo, prop, tipo_n, desc, dir_, ciudad, zona, precio, sup, hab, banos, garaje, estado) in enumerate(inmuebles_data, 1):
        direccion_obj = Direccion.objects.create(
            ciudad=ciudad,
            zona=zona,
            calle=dir_
        )

        gps_val = '-17.799690252631134, -63.1928899884224' if titulo == 'Casa zona 2do anillo' else f'-16.5{idx:03d}, -68.0{idx:03d}'
        largo_val = Decimal('150.00') if titulo == 'Casa zona 2do anillo' else None
        ancho_val = Decimal('75.00') if titulo == 'Casa zona 2do anillo' else None

        inm, _ = Inmueble.objects.get_or_create(
            titulo=titulo,
            defaults={
                'propietario': users[prop], 'tipo': tipos[tipo_n],
                'descripcion': desc,
                'direccion': direccion_obj,
                'superficie': Decimal(str(sup)), 'habitaciones': hab,
                'banos': banos, 'garaje': garaje, 'estado': estado,
                'gps': gps_val,
                'largo': largo_val,
                'ancho': ancho_val,
                'modelo_3d': 'https://raw.githubusercontent.com/GoogleWebComponents/model-viewer/master/packages/shared-assets/models/Astronaut.glb' if idx == 1 else None
            }
        )
        
        tipo_oferta = 'venta' if ('venta' in titulo.lower() or 'terreno' in titulo.lower() or idx in [3, 8, 9]) else 'alquiler'
        if idx == 7:
            tipo_oferta = 'anticretico'
            
        # Asignar precio comercial realista basado en el tipo de oferta
        if tipo_oferta == 'alquiler':
            if idx == 1:
                precio_comercial = Decimal('3500.00')
            elif idx == 4:
                precio_comercial = Decimal('4500.00')
            elif idx == 6:
                precio_comercial = Decimal('5500.00')
            elif idx == 10:
                precio_comercial = Decimal('6500.00')
            else:
                precio_comercial = Decimal('2800.00')
        elif tipo_oferta == 'anticretico':
            precio_comercial = Decimal('80000.00')
        else:
            precio_comercial = Decimal(str(precio))

        Publicacion.objects.get_or_create(
            inmueble=inm,
            estado=Publicacion.EstadoPublicacion.ACTIVA,
            defaults={
                'tipo_oferta': tipo_oferta,
                'precio': precio_comercial,
            }
        )
        
        inmuebles[titulo] = inm
    print(f"  OK Inmuebles: {len(inmuebles)} (1-10, 1 por usuario)")


    # ═══════════════════════════════════════════════════════════
    #  MULTIMEDIA (fotos por inmueble)
    # ═══════════════════════════════════════════════════════════
    multimedia_data = [
        # Inmueble 1: Casa Moderna Zona Sur (IDs 1-7)
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/ngmi72br9ceznkr48wao.jpg", False),
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/do4mjosrvqwxyjfmw6io.jpg", False),
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/uf4sednyadjsdy9n3zbm.jpg", False),
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/rlv2vl173nypaujonuqc.jpg", False),
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445026/hmoqw6ko1ihz0fchikds.jpg", False),
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445026/nlzxtzajf1v8sdhersrj.jpg", False),
        (1, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445026/lcfrxmxdzhfnehsmqezx.jpg", True),
        # Inmueble 2: Depto Miraflores 2 Hab (ID 8)
        (2, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445301/h4cmv5jeaee22roathor.jpg", True),
        # Inmueble 3: Casa Colonial San Jorge (IDs 9-12)
        (3, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445650/n2jqn1liu6piuiuouiqr.jpg", False),
        (3, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445652/c05zvion4415uhrzbgep.jpg", True),
        (3, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445652/xsspbrwnzvnjlw6oanbd.jpg", False),
        (3, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445652/ogdi0odon4m2iwj9wmoi.jpg", False),
        # Inmueble 4: Casa Familiar Achumani (ID 13)
        (4, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776445789/bjth7eibw9cvjc7wfkmt.jpg", True),
        # Inmueble 5: Depto Penthouse Calacoto (IDs 14-18)
        (5, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446045/ai1unubgqrgifa2l2hyf.jpg", True),
        (5, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446047/ehpfydealejrphlmk7yt.jpg", False),
        (5, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446047/obhxra8gwngvtuuju60b.jpg", False),
        (5, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446047/pvx1i82oebr7rztn9s2f.jpg", False),
        (5, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446047/cft7obruommbutsadogb.jpg", False),
        # Inmueble 6: Casa con Jardín Seguencoma (IDs 19-21)
        (6, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446334/esuk1ezntp9yjk8mn9b6.jpg", True),
        (6, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446336/f49b9w8o7xsl2ttpceta.jpg", False),
        (6, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446336/imxgtvh68hfzjhzhx0kb.jpg", False),
        # Inmueble 7: Depto Nuevo San Miguel (IDs 22-26)
        (7, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446463/ocvj9wv2hdqgpzeakrbe.jpg", True),
        (7, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446465/hc0f5apxptadjvvvka0c.jpg", False),
        (7, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446465/lzao70ngntltxxzmzoyb.jpg", False),
        (7, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446465/b7dmv39ul8awohqoyenj.jpg", False),
        (7, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446465/s1wb1eno2t2fnecheoud.jpg", False),
        # Inmueble 8: Casa Minimalista Obrajes (IDs 27-31)
        (8, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446669/tq3lgvgnjgqphh4lydij.jpg", False),
        (8, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446669/dvrfjwxpmwq13svlkmf5.jpg", False),
        (8, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446669/tgzjwumx1rdrkspeuxh9.jpg", False),
        (8, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446674/olzbfbvcdrnkquvk0nuu.jpg", True),
        (8, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446678/tz5rd1xrpcmdfst11rqh.jpg", False),
        # Inmueble 9: Depto Familiar Irpavi (IDs 32-38)
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446846/f9b1ixrqmhjkjhnbojxh.jpg", True),
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446847/xrc8qgplvhorwmremvco.jpg", False),
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446848/uej0www3ynl2bjatfjae.jpg", False),
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446848/wis7almtxjxfmidhx0j9.jpg", False),
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446848/v1a3vs07v9b2mlpjlqo1.jpg", False),
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446848/kgpqam7ly6tayz9zohkf.jpg", False),
        (9, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776446848/xbyv4abtliuk4bpusnbk.jpg", False),
        # Inmueble 10: Loft Artístico Sopocachi (IDs 39-41)
        (10, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776447047/wtaztxodqjrfgakvwhan.jpg", True),
        (10, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776447049/che9u7laxv2l49j6vgba.jpg", False),
        (10, "https://res.cloudinary.com/dwerzrgya/image/upload/v1776447049/brwg9ljso5osrt443qzp.jpg", False),
        # Inmueble 11: Casa zona 2do anillo (ID 11)
        (11, "https://res.cloudinary.com/dwerzrgya/image/upload/v1781387317/v9j2lcylveshcrk5kb8d.jpg", True),
    ]
    
    media_count = 0
    for inm_id, archivo, principal in multimedia_data:
        # Obtener el inmueble por orden de creación (1-10)
        inm_list = list(inmuebles.values())
        if inm_id <= len(inm_list):
            inm = inm_list[inm_id - 1]
            Multimedia.objects.get_or_create(
                inmueble=inm,
                archivo=archivo,
                defaults={'principal': principal, 'tipo': 'imagen'}
            )
            media_count += 1
    print(f"  OK Multimedia: {media_count} fotos asignadas")

    # ═══════════════════════════════════════════════════════════
    #  TIPOS DE CONTRATO
    # ═══════════════════════════════════════════════════════════
    tipos_contrato_data = [
        ('Alquiler', 'Contrato de arrendamiento mensual o anual.'),
        ('Venta', 'Contrato de compraventa de inmueble.'),
        ('Anticrético', 'Contrato de anticresis con depósito como garantía.'),
        ('Contrato Mixto', 'Combinación de alquiler con opción de compra.'),
        ('Traspaso', 'Transferencia de derechos de uso sobre un local comercial.'),
        ('Comodato', 'Préstamo de uso gratuito por un tiempo determinado.'),
    ]
    t_contratos = {}
    for nombre, desc in tipos_contrato_data:
        tc, _ = TipoContrato.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc})
        t_contratos[nombre] = tc
    print(f"  OK Tipos de Contrato: {len(t_contratos)}")

    # ═══════════════════════════════════════════════════════════
    #  CONTRATOS (5 contratos entre usuarios e inmuebles)
    # ═══════════════════════════════════════════════════════════
    inm_list = list(inmuebles.values())
    contratos_data = [
        (0, 'propietario1', 'Alquiler', -30, 365, 3500, 7000, 'activo'),
        (1, 'propietario2', 'Alquiler', -60, 330, 1800, 3600, 'activo'),
        (2, 'propietario3', 'Anticrético', -15, 400, 0, 25000, 'activo'),
        (4, 'propietario5', 'Venta', -90, 0, 450000, 0, 'pendiente'),
        (5, 'propietario6', 'Contrato Mixto', -20, 360, 4500, 15000, 'activo'),
    ]
    contratos = {}
    for inm_idx, inq_uname, tipo_c, offset_ini, dur, monto, dep, estado in contratos_data:
        if inm_idx < len(inm_list):
            c, created = Contrato.objects.get_or_create(
                inmueble=inm_list[inm_idx], inquilino=users[inq_uname],
                defaults={
                    'tipo_contrato': t_contratos[tipo_c],
                    'inicio': date.today() + timedelta(days=offset_ini),
                    'fin': date.today() + timedelta(days=offset_ini + dur) if dur > 0 else None,
                    'monto': Decimal(str(monto)), 'deposito': Decimal(str(dep)),
                    'estado': estado,
                }
            )
            contratos[inm_idx] = c
    print(f"  OK Contratos: {len(contratos)}")

    # ═══════════════════════════════════════════════════════════
    #  TIPOS DE PAGO
    # ═══════════════════════════════════════════════════════════
    tipos_pago_data = [
        ('Efectivo', 'Pago en efectivo en oficina.', True),
        ('Transferencia Bancaria', 'Transferencia a cuenta del propietario.', True),
        ('QR', 'Pago mediante código QR.', True),
        ('Tarjeta de Crédito', 'Pago con tarjeta de crédito o débito.', True),
        ('Cheque', 'Pago mediante cheque bancario.', False),
    ]
    t_pagos = {}
    for nombre, desc, activo in tipos_pago_data:
        tp, _ = TipoPago.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc, 'activo': activo})
        t_pagos[nombre] = tp
    print(f"  OK Tipos de Pago: {len(t_pagos)}")

    # ═══════════════════════════════════════════════════════════
    #  PAGOS (8 pagos de contratos)
    # ═══════════════════════════════════════════════════════════
    pagos_data = [
        (0, 'propietario1', 'Efectivo', 3500, 0, 'completado', 'Pago mes 1'),
        (0, 'propietario1', 'Transferencia Bancaria', 3500, -30, 'completado', 'Pago mes 2'),
        (0, 'propietario1', 'QR', 3500, -60, 'completado', 'Pago mes 3'),
        (1, 'propietario2', 'Efectivo', 1800, 0, 'completado', 'Primer mes'),
        (1, 'propietario2', 'Transferencia Bancaria', 1800, -30, 'pendiente', 'Segundo mes'),
        (4, 'propietario5', 'Tarjeta de Crédito', 450000, -5, 'completado', 'Adelanto venta'),
        (5, 'propietario6', 'QR', 4500, -10, 'completado', 'Cuota mensual'),
        (5, 'propietario6', 'Efectivo', 4500, -40, 'completado', 'Cuota anterior'),
    ]
    pagos = []
    for inm_idx, usr, tp_nombre, monto, offset, estado, obs in pagos_data:
        if inm_idx in contratos:
            pago, created = Pago.objects.get_or_create(
                contrato=contratos[inm_idx],
                usuario=users[usr],
                fecha=date.today() + timedelta(days=offset),
                monto=Decimal(str(monto)),
                defaults={
                    'tipo_pago': t_pagos[tp_nombre], 'estado': estado,
                    'observaciones': obs,
                }
            )
            pagos.append(pago)
    print(f"  OK Pagos: {len(pagos)}")

    # ═══════════════════════════════════════════════════════════
    #  HISTORIAL DE PAGOS
    # ═══════════════════════════════════════════════════════════
    for pago in pagos[:4]:
        HistorialPago.objects.get_or_create(
            pago=pago,
            defaults={
                'anterior': 'pendiente', 'nuevo': 'completado',
                'comentario': 'Pago verificado y aprobado.', 'usuario': admin
            }
        )
    print("  OK Historial de pagos: 4 registros")

    # ═══════════════════════════════════════════════════════════
    #  COMISIONES TRANSACCIONALES
    # ═══════════════════════════════════════════════════════════
    comision_count = 0
    porcentaje_base = config.porcentaje_comision_plataforma
    for p in Pago.objects.filter(estado='completado'):
        monto_comision = p.monto * (Decimal(porcentaje_base) / Decimal('100'))
        monto_comision = round(monto_comision, 2)
        comision = Comision.objects.create(
            contrato=p.contrato,
            pago=p,
            porcentaje=porcentaje_base,
            monto=monto_comision,
            descripcion=f"Comisión automática del {porcentaje_base}% por pago #{p.id}",
            pagada=True
        )
        # Forzar la fecha para que coincida con la del pago
        Comision.objects.filter(id=comision.id).update(fecha=p.fecha)
        comision_count += 1
    print(f"  OK Comisiones generadas: {comision_count} registros")

    # ═══════════════════════════════════════════════════════════
    #  AGENDA (8 eventos)
    # ═══════════════════════════════════════════════════════════
    # pyrefly: ignore [missing-import]
    from django.utils import timezone
    agenda_data = [
        ('admin', 'Reunión con propietarios', 'Reunión mensual de revisión de propiedades.', 1, 2, 'Oficina Central', False),
        ('propietario1', 'Inspección Casa Moderna', 'Verificar estado del inmueble antes de publicar.', 3, 4, 'Calacoto, La Paz', False),
        ('propietario2', 'Visita de cliente', 'Cliente interesado en departamento.', 2, 3, 'Miraflores', False),
        ('propietario3', 'Firmar contrato alquiler', 'Firma de contrato con nuevo inquilino.', 5, 6, 'Notaría San Jorge', False),
        ('propietario4', 'Mantenimiento propiedad', 'Revisión de servicios e instalaciones.', 0, 0, 'Achumani', False),
        ('propietario5', 'Sesión fotográfica', 'Tomar fotos profesionales del inmueble.', 4, 5, 'Calacoto', False),
        ('propietario6', 'Revisión de contrato', 'Revisar términos del nuevo contrato.', 1, 2, 'Oficina', False),
        ('admin', 'Capacitación usuarios', 'Entrenar a nuevos propietarios en el sistema.', 7, 9, 'Remoto', False),
    ]
    for usr, titulo, desc, di, df, ubic, comp in agenda_data:
        Agenda.objects.get_or_create(
            usuario=users[usr], titulo=titulo,
            defaults={
                'descripcion': desc,
                'inicio': timezone.now() + timedelta(days=di, hours=9),
                'fin': timezone.now() + timedelta(days=df, hours=11),
                'ubicacion': ubic, 'completado': comp,
            }
        )
    print(f"  OK Eventos de agenda: {len(agenda_data)}")

    # ═══════════════════════════════════════════════════════════
    #  NOTIFICACIONES (10 notificaciones)
    # ═══════════════════════════════════════════════════════════
    notif_data = [
        ('propietario1', 'pago', 'Pago de alquiler pendiente', 'Tu pago de alquiler vence en 3 días.'),
        ('propietario2', 'recordatorio', 'Vence tu contrato', 'Tu contrato de alquiler vence próximamente.'),
        ('propietario3', 'info', 'Nueva solicitud de visita', 'Un usuario solicita visitar tu propiedad.'),
        ('propietario4', 'info', 'Inmueble destacado', 'Tu casa fue destacada en el portal esta semana.'),
        ('propietario5', 'alerta', 'Precio actualizado', 'Tu inmueble actualizó su precio.'),
        ('propietario6', 'info', 'Documentación pendiente', 'Necesitas completar tu perfil.'),
        ('propietario7', 'recordatorio', 'Visita programada', 'Tienes una visita programada mañana.'),
        ('propietario8', 'alerta', 'Nuevo usuario interesado', 'Un nuevo usuario está interesado en tu propiedad.'),
        ('propietario9', 'info', 'Publicaciones por revisar', 'Hay inmuebles pendientes de aprobación.'),
        ('muerte', 'alerta', 'Alerta de seguridad', 'Se detectó acceso inusual a tu cuenta.'),
    ]
    for usr, tipo, titulo, mensaje in notif_data:
        Notificacion.objects.get_or_create(
            usuario=users[usr], titulo=titulo,
            defaults={'tipo': tipo, 'mensaje': mensaje, 'leida': False}
        )
    print(f"  OK Notificaciones: {len(notif_data)}")

    # ═══════════════════════════════════════════════════════════
    #  CHATS Y MENSAJES (4 chats con múltiples mensajes)
    # ═══════════════════════════════════════════════════════════
    chats_data = [
        ('propietario1', 'propietario2', 0, [
            ('propietario1', 'texto', 'Hola, me interesa tu casa en zona sur.', ''),
            ('propietario2', 'texto', '¡Hola! Sí, la casa está disponible. ¿Cuándo te gustaría visitarla?', ''),
            ('propietario1', 'texto', '¿Puede ser este sábado por la mañana?', ''),
            ('propietario2', 'texto', 'Perfecto, te espero a las 10:00 AM.', ''),
        ]),
        ('propietario3', 'propietario4', 2, [
            ('propietario3', 'texto', 'Hola, me interesa tu propiedad en San Jorge.', ''),
            ('propietario4', 'texto', 'Buenas, sí está disponible. ¿Tienes preguntas?', ''),
            ('propietario3', 'texto', 'Sí, ¿cuál es el precio de alquiler mensual?', ''),
            ('propietario4', 'texto', 'El alquiler es Bs. 3500 mensuales con depósito.', ''),
        ]),
        ('propietario5', 'propietario6', 4, [
            ('propietario5', 'texto', 'Hola, vi tu penthouse, se ve increíble.', ''),
            ('propietario6', 'texto', 'Gracias, es una de nuestras mejores propiedades.', ''),
            ('propietario5', 'texto', '¿Hay posibilidad de visita esta semana?', ''),
            ('propietario6', 'texto', 'Claro, disponible mañana a las 3 PM.', ''),
        ]),
        ('propietario7', 'propietario8', 6, [
            ('propietario7', 'texto', 'Hola, tengo un problema con la propiedad.', ''),
            ('propietario8', 'texto', 'Claro, ¿cuál es el problema?', ''),
            ('propietario7', 'texto', 'La cerradura no funciona correctamente.', ''),
            ('propietario8', 'texto', 'Enviaré un cerrajero mañana temprano.', ''),
        ]),
    ]
    chats_count = 0
    for p1_uname, p2_uname, inm_idx, msgs in chats_data:
        inm = inm_list[inm_idx] if inm_idx < len(inm_list) else None
        chat, _ = Chat.objects.get_or_create(
            participante1=users[p1_uname],
            participante2=users[p2_uname],
            defaults={'inmueble': inm}
        )
        for rem_uname, tipo_msg, contenido, ubicacion in msgs:
            Mensaje.objects.get_or_create(
                chat=chat,
                remitente=users[rem_uname],
                contenido=contenido,
                defaults={
                    'tipo': tipo_msg,
                    'ubicacion': ubicacion,
                }
            )
        chats_count += 1
    print(f"  OK Chats: {chats_count} (con 16 mensajes)")

    # ═══════════════════════════════════════════════════════════
    #  RESEÑAS (10 reseñas de inmuebles)
    # ═══════════════════════════════════════════════════════════
    resenas_data = [
        ('propietario1', 0, 5, 'Increíble propiedad, muy bien mantenida.'),
        ('propietario2', 0, 4, 'Muy buena casa, pero el acceso es complicado.'),
        ('propietario3', 2, 5, 'Hermosa casa colonial, perfecta para vivir.'),
        ('propietario4', 3, 4, 'Buena ubicación, ambiente tranquilo.'),
        ('propietario5', 4, 5, 'El penthouse es increíble, vista panorámica.'),
        ('propietario6', 1, 3, 'Departamento funcional pero pequeño.'),
        ('propietario7', 5, 4, 'Un espacio muy creativo y bien diseñado.'),
        ('propietario8', 3, 5, 'Excelente zona residencial, muy tranquila.'),
        ('propietario9', 6, 4, 'Ubicación céntrica, muy práctica.'),
        ('muerte', 9, 5, 'Loft artístico, estilo muy especial.'),
    ]
    for usr, inm_idx, calif, com in resenas_data:
        if inm_idx < len(inm_list):
            Resena.objects.get_or_create(
                usuario=users[usr],
                inmueble=inm_list[inm_idx],
                defaults={'calificacion': calif, 'comentario': com}
            )
    print(f"  OK Reseñas: {len(resenas_data)}")

    # ═══════════════════════════════════════════════════════════
    #  BLOQUEOS (2 bloqueos de usuarios)
    # ═══════════════════════════════════════════════════════════
    Bloqueo.objects.get_or_create(
        bloqueador=users['propietario1'],
        bloqueado=users['propietario9'],
        defaults={}
    )
    Bloqueo.objects.get_or_create(
        bloqueador=users['propietario5'],
        bloqueado=users['muerte'],
        defaults={}
    )
    print("  OK Bloqueos de usuarios: 2")

    # ═══════════════════════════════════════════════════════════
    #  NUEVAS TABLAS ADICIONALES
    # ═══════════════════════════════════════════════════════════
    from datetime import time
    from django.utils import timezone

    # 1. PANORAMAS 360 y HOTSPOTS
    print("Creando panoramas y hotspots...")
    inm_1 = inm_list[0]
    pan1, _ = Multimedia.objects.get_or_create(
        inmueble=inm_1,
        archivo="https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/panorama1.jpg",
        defaults={'principal': False, 'tipo': 'panorama360', 'descripcion': 'Sala Principal 360'}
    )
    pan2, _ = Multimedia.objects.get_or_create(
        inmueble=inm_1,
        archivo="https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/panorama2.jpg",
        defaults={'principal': False, 'tipo': 'panorama360', 'descripcion': 'Cocina Americana 360'}
    )
    
    Hotspot.objects.get_or_create(
        inmueble=inm_1,
        escena_origen=pan1,
        escena_destino=pan2,
        defaults={
            'pitch': 10.0,
            'yaw': 45.0,
            'texto_ayuda': 'Ir a Cocina'
        }
    )
    Hotspot.objects.get_or_create(
        inmueble=inm_1,
        escena_origen=pan2,
        escena_destino=pan1,
        defaults={
            'pitch': -5.0,
            'yaw': 180.0,
            'texto_ayuda': 'Volver a Sala'
        }
    )
    print("  OK Hotspots creados: 2")

    # 2. FAVORITOS
    Favorito.objects.get_or_create(usuario=users['propietario2'], inmueble=inm_list[0])
    Favorito.objects.get_or_create(usuario=users['propietario3'], inmueble=inm_list[1])
    print("  OK Favoritos creados: 2")

    # 3. CITAS
    Cita.objects.get_or_create(
        inmueble=inm_list[0],
        fecha=date.today() + timedelta(days=2),
        hora_inicio=time(14, 0),
        defaults={
            'cliente': users['propietario2'],
            'propietario': inm_list[0].propietario,
            'hora_fin': time(15, 0),
            'estado': 'pendiente',
            'notas': 'Visita guiada para ver acabados de la cocina.'
        }
    )
    Cita.objects.get_or_create(
        inmueble=inm_list[1],
        fecha=date.today() + timedelta(days=3),
        hora_inicio=time(10, 0),
        defaults={
            'cliente': users['propietario3'],
            'propietario': inm_list[1].propietario,
            'hora_fin': time(11, 0),
            'estado': 'confirmada',
            'notas': 'Llevar documentos originales.'
        }
    )
    print("  OK Citas creadas: 2")

    # 4. HORARIOS DISPONIBLES
    HorarioDisponible.objects.get_or_create(
        propietario=users['propietario1'],
        dia_semana=0,
        hora_inicio=time(9, 0),
        hora_fin=time(12, 0),
        defaults={'activo': True}
    )
    HorarioDisponible.objects.get_or_create(
        propietario=users['propietario1'],
        dia_semana=5,
        hora_inicio=time(14, 0),
        hora_fin=time(18, 0),
        defaults={'activo': True}
    )
    print("  OK Horarios Disponibles creados: 2")

    # 5. VERIFICACIONES DE TÍTULO
    VerificacionTitulo.objects.get_or_create(
        inmueble=inm_list[0],
        defaults={
            'solicitado_por': users['propietario1'],
            'archivo_titulo': 'https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/titulo1.pdf',
            'texto_ocr': 'Folio Real Matrícula 701101234. Propietario: Juan Pérez. Gravámenes: Ninguno.',
            'resultado_ia': {'valido': True, 'analisis': 'Documento legalmente verificado y libre de gravamen.'},
            'estado': 'verificado',
            'score_confianza': 98,
            'resumen_publico': 'Título de propiedad verificado libre de cargas.'
        }
    )
    print("  OK Verificaciones de Título creadas: 1")

    # 6. ACCESOS RECORRIDO 360
    AccesoRecorrido360.objects.get_or_create(
        inmueble=inm_list[0],
        cliente=users['propietario2'],
        propietario=users['propietario1'],
        defaults={
            'fecha_expiracion': timezone.now() + timedelta(days=7),
            'activo': True,
            'visitas': 2
        }
    )
    print("  OK Accesos Recorrido 360 creados: 1")

    # 7. DETALLES DE PAGO
    for p in Pago.objects.all()[:3]:
        DetallePago.objects.get_or_create(
            pago=p,
            concepto='Alquiler mensual básico',
            defaults={'monto': p.monto}
        )
    print("  OK Detalles de Pago creados: 3")

    # 8. PLANES DE SUSCRIPCIÓN
    tp_mensual, _ = TipoPlan.objects.get_or_create(nombre='Mensual', defaults={'descripcion': 'Planes de cobro mensual'})
    tp_anual, _ = TipoPlan.objects.get_or_create(nombre='Anual', defaults={'descripcion': 'Planes de cobro anual con descuento'})
    
    Plan.objects.get_or_create(
        nombre='Plan Básico',
        precio=Decimal('99.00'),
        defaults={
            'tipo_plan': tp_mensual,
            'descripcion': 'Hasta 5 inmuebles.',
            'duracion': 1,
            'max_inmuebles': 5,
            'max_usuarios': 1,
            'activo': True
        }
    )
    Plan.objects.get_or_create(
        nombre='Plan Premium',
        precio=Decimal('299.00'),
        defaults={
            'tipo_plan': tp_mensual,
            'descripcion': 'Inmuebles ilimitados y soporte prioritario.',
            'duracion': 1,
            'max_inmuebles': 100,
            'max_usuarios': 5,
            'activo': True
        }
    )
    print("  OK Planes de Suscripción creados: 2")

    # 9. TRANSACCIONES STRIPE
    contrato_stripe = list(contratos.values())[0]
    TransaccionStripe.objects.get_or_create(
        stripe_session_id='cs_test_a1b2c3d4e5f6',
        defaults={
            'contrato': contrato_stripe,
            'pagador': contrato_stripe.inquilino,
            'propietario': contrato_stripe.inmueble.propietario,
            'tipo_operacion': 'alquiler',
            'monto': contrato_stripe.monto,
            'moneda': 'usd',
            'descripcion': 'Pago de mensualidad mediante Stripe checkout',
            'stripe_payment_intent': 'pi_test_123456789',
            'estado': 'completada'
        }
    )
    print("  OK Transacciones Stripe creadas: 1")

    print("\n  OK Datos semilla creados exitosamente.")
    print("  ----------------------------------------------")
    print("  [+] USUARIOS:           12 (admin + diego + 10 propietarios)")
    print("  [+] INMUEBLES:          11 (Santa Cruz y La Guardia, 1 por usuario)")
    print("  [+] MULTIMEDIA:         43 fotos (incluyendo 2 panoramas 360 y foto de diego)")
    print("  [+] HOTSPOTS:           2 puntos de navegación 360")
    print("  [+] FAVORITOS:          2 registrados")
    print("  [+] CITAS:              2 agendadas")
    print("  [+] HORARIOS DISP.:     2 configurados")
    print("  [+] VERIF. TÍTULOS:     1 verificada en blockchain")
    print("  [+] ACCESOS 360:        1 activo")
    print("  [+] CONTRATOS:          5 (Alquiler, Venta, Anticretico, Mixto)")
    print("  [+] PAGOS:              8 (con desglose de detalles)")
    print("  [+] AGENDA:             8 eventos programados")
    print("  [+] NOTIFICACIONES:     10 alertas")
    print("  [+] CHATS:              4 (con 16 mensajes)")
    print("  [+] RESENAS:            10 calificaciones")
    print("  [+] BLOQUEOS:           2 usuarios bloqueados")
    print("  [+] PLANES / SUSC.:     2 planes comerciales")
    print("  [+] STRIPE TXS:         1 transacción de prueba")
    print("  ----------------------------------------------")
    print("  [!] Acceso Admin:       admin@autogestion.bo / admin123")
    print("  [!] Otros usuarios:     usuario123")
    print("  ----------------------------------------------")


if __name__ == '__main__':
    create_seed_data()
