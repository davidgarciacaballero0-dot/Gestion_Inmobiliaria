from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pagos', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelTable(name='tipopago', table='pagos_tipo_pago'),
        migrations.AlterModelTable(name='pago', table='pagos_pago'),
        migrations.AlterModelTable(name='detallepago', table='pagos_detalle_pago'),
        migrations.AlterModelTable(name='historialpago', table='pagos_historial_pago'),
        migrations.AlterModelTable(name='tipoplan', table='pagos_tipo_plan'),
        migrations.AlterModelTable(name='plan', table='pagos_plan'),
    ]
