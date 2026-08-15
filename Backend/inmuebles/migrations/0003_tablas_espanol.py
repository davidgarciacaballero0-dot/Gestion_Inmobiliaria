from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inmuebles', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelTable(name='tipoinmueble', table='inmuebles_tipo_inmueble'),
        migrations.AlterModelTable(name='direccion', table='inmuebles_direccion'),
        migrations.AlterModelTable(name='inmueble', table='inmuebles_inmueble'),
        migrations.AlterModelTable(name='multimedia', table='inmuebles_multimedia'),
        migrations.AlterModelTable(name='tipocontrato', table='inmuebles_tipo_contrato'),
        migrations.AlterModelTable(name='contrato', table='inmuebles_contrato'),
        migrations.AlterModelTable(name='comision', table='inmuebles_comision'),
        migrations.AlterModelTable(name='favorito', table='inmuebles_favorito'),
    ]
