# Generated by Django 3.2.18 on 2023-12-15 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sortides', '0028_alter_sortida_tipus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sortida',
            name='tipus',
            field=models.CharField(choices=[('A', 'Activitat'), ('M', 'Material'), ('T', 'Matrícula')], default='E', help_text="Tipus d'activitat", max_length=1),
        ),
    ]
