"""
fix_panoramas.py
================
Script para:
1. Subir 2 imagenes panoramicas equirectangulares 360 desde URLs publicas a Cloudinary.
2. Actualizar las URLs en la base de datos (tabla inmuebles_multimedia).
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import django
django.setup()

import cloudinary
import cloudinary.uploader
import cloudinary.api
from inmuebles.models import Multimedia

# Configuracion de Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dwerzrgya'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '581815563668339'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'ul_5HAkewevM14trmtf7onSxZtU'),
    secure=True
)

# Imagenes de habitaciones de Unsplash (dominio publico, alta resolucion)
# Se usaran como panoramas de muestra (proporcion 2:1 simulada)
PANORAMAS_REALES = [
    {
        'public_id': 'autogestion/panorama1_sala',
        'url_origen': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=4096&q=80',
        'descripcion': 'Sala Principal 360',
        'url_antigua': 'https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/panorama1.jpg',
    },
    {
        'public_id': 'autogestion/panorama2_cocina',
        'url_origen': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=4096&q=80',
        'descripcion': 'Cocina Americana 360',
        'url_antigua': 'https://res.cloudinary.com/dwerzrgya/image/upload/v1776445025/panorama2.jpg',
    },
]

URLS_RESPALDO = [
    'https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg?auto=compress&cs=tinysrgb&w=4096',
    'https://images.pexels.com/photos/2089698/pexels-photo-2089698.jpeg?auto=compress&cs=tinysrgb&w=4096',
]


def subir_a_cloudinary(public_id, url_origen):
    print("  Subiendo '%s' desde URL remota..." % public_id)
    result = cloudinary.uploader.upload(
        url_origen,
        public_id=public_id,
        overwrite=True,
        resource_type='image',
        tags=['panorama360', 'autogestion']
    )
    secure_url = result['secure_url']
    print("  OK: %s" % secure_url)
    return secure_url


def actualizar_bd(url_antigua, url_nueva):
    n = Multimedia.objects.filter(archivo=url_antigua).update(archivo=url_nueva)
    print("  BD actualizada: %d registro(s)" % n)
    return n


def main():
    print("=" * 60)
    print("  FIX PANORAMAS 360 - Autogestion Inmobiliaria")
    print("=" * 60)

    print("\n[1/3] Verificando conexion a Cloudinary...")
    try:
        info = cloudinary.api.ping()
        print("  Cloudinary OK: %s" % info)
    except Exception as e:
        print("  ERROR conectando a Cloudinary: %s" % e)
        sys.exit(1)

    print("\n[2/3] Subiendo imagenes a Cloudinary...")
    urls_nuevas = {}

    for i, pano in enumerate(PANORAMAS_REALES):
        try:
            url_nueva = subir_a_cloudinary(pano['public_id'], pano['url_origen'])
            urls_nuevas[pano['url_antigua']] = url_nueva
        except Exception as e:
            print("  FALLO con URL primaria: %s" % e)
            print("  Intentando con URL de respaldo...")
            try:
                url_nueva = subir_a_cloudinary(pano['public_id'] + '_bk', URLS_RESPALDO[i])
                urls_nuevas[pano['url_antigua']] = url_nueva
            except Exception as e2:
                print("  TAMBIEN FALLO el respaldo: %s" % e2)

    print("\n[3/3] Actualizando URLs en la base de datos...")
    total = 0
    for url_antigua, url_nueva in urls_nuevas.items():
        total += actualizar_bd(url_antigua, url_nueva)

    print("\n" + "=" * 60)
    print("  COMPLETADO. Registros actualizados: %d" % total)
    print("\n  Panoramas 360 actuales en BD:")
    for p in Multimedia.objects.filter(tipo='panorama360'):
        print("    ID %d | %s: %s" % (p.id, p.descripcion, p.archivo[:100]))
    print("=" * 60)


if __name__ == '__main__':
    main()
