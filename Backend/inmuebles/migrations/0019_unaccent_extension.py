# Generated manually
from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension

class Migration(migrations.Migration):

    dependencies = [
        ('inmuebles', '0018_alter_multimedia_tipo'),
    ]

    operations = [
        UnaccentExtension(),
    ]
