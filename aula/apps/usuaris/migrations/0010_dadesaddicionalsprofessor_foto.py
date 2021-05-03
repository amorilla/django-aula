# Generated by Django 3.1.2 on 2020-12-07 09:08

from django.db import migrations
import private_storage.fields
import private_storage.storage.files


class Migration(migrations.Migration):

    dependencies = [
        ('usuaris', '0009_auto_20200405_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='dadesaddicionalsprofessor',
            name='foto',
            field=private_storage.fields.PrivateFileField(blank=True, null=True, storage=private_storage.storage.files.PrivateFileSystemStorage(), upload_to='profes/fotos', verbose_name='Foto'),
        ),
    ]