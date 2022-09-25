# Generated by Django 4.0.2 on 2022-08-04 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matricula', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matricula',
            name='adreca',
            field=models.CharField(blank=True, default='', max_length=250, verbose_name='Adreça'),
        ),
        migrations.AlterField(
            model_name='matricula',
            name='cp',
            field=models.CharField(blank=True, default='', max_length=10, verbose_name='Codi postal'),
        ),
        migrations.AlterField(
            model_name='matricula',
            name='localitat',
            field=models.CharField(blank=True, default='', max_length=250, verbose_name='Localitat'),
        ),
        migrations.AlterField(
            model_name='matricula',
            name='rp1_correu',
            field=models.EmailField(blank=True, default='', max_length=254, verbose_name='Correu 1r responsable'),
        ),
        migrations.AlterField(
            model_name='matricula',
            name='rp1_nom',
            field=models.CharField(blank=True, default='', max_length=250, verbose_name='Nom complet 1r responsable'),
        ),
        migrations.AlterField(
            model_name='matricula',
            name='rp1_telefon',
            field=models.CharField(blank=True, default='', max_length=15, verbose_name='Telèfon 1r responsable'),
        ),
    ]