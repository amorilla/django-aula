# Generated by Django 3.2.18 on 2023-12-24 20:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sortides', '0031_sortida_subtipus'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sortida',
            old_name='titol_de_la_sortida',
            new_name='titol',
        ),
    ]
