from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(name='usuario', table='usuarios_usuario'),
        migrations.AlterModelTable(name='agenda', table='usuarios_agenda'),
        migrations.AlterModelTable(name='notificacion', table='usuarios_notificacion'),
        migrations.AlterModelTable(name='bloqueo', table='usuarios_bloqueo'),
        migrations.AlterModelTable(name='chat', table='usuarios_conversacion'),
        migrations.AlterModelTable(name='mensaje', table='usuarios_mensaje'),
        migrations.AlterModelTable(name='resena', table='usuarios_resena'),
    ]
