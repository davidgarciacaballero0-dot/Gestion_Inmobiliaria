from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inmuebles', '0005_contrato_actualizado_contrato_chat_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HorarioDisponible',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('dia_semana', models.IntegerField(choices=[
                    (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
                    (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
                ])),
                ('hora_inicio', models.TimeField()),
                ('hora_fin',    models.TimeField()),
                ('activo',      models.BooleanField(default=True)),
                ('propietario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='horarios_disponibles',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('inmueble', models.ForeignKey(
                    blank=True, null=True,
                    help_text='Si es nulo, aplica a todos los inmuebles del propietario',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='horarios_disponibles',
                    to='inmuebles.inmueble',
                )),
            ],
            options={
                'verbose_name': 'Horario Disponible',
                'verbose_name_plural': 'Horarios Disponibles',
                'db_table': 'inmuebles_horario_disponible',
                'ordering': ['dia_semana', 'hora_inicio'],
            },
        ),
        migrations.CreateModel(
            name='Cita',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('fecha',       models.DateField()),
                ('hora_inicio', models.TimeField()),
                ('hora_fin',    models.TimeField()),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente',  'Pendiente'),
                        ('confirmada', 'Confirmada'),
                        ('cancelada',  'Cancelada'),
                        ('completada', 'Completada'),
                    ],
                    default='pendiente', max_length=20,
                )),
                ('notas',       models.TextField(blank=True)),
                ('creado',      models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('inmueble', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='citas', to='inmuebles.inmueble',
                )),
                ('cliente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='citas_como_cliente', to=settings.AUTH_USER_MODEL,
                )),
                ('propietario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='citas_como_propietario', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Cita',
                'verbose_name_plural': 'Citas',
                'db_table': 'inmuebles_cita',
                'ordering': ['fecha', 'hora_inicio'],
                'unique_together': {('inmueble', 'fecha', 'hora_inicio')},
            },
        ),
    ]