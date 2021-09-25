# Generated by Django 3.2.5 on 2021-07-26 01:21

import aula.apps.sortides.models
from django.db import migrations, models
import django.db.models.deletion
import private_storage.fields
import private_storage.storage.files


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('alumnes', '0015_auto_20210726_0121'),
        ('sortides', '0024_auto_20210417_1323'),
        ('extPreinscripcio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Matricula',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idAlumne', models.CharField(max_length=15, verbose_name="RALC de l'alumne")),
                ('estat', models.CharField(choices=[('A', 'Acceptada'), ('F', 'Finalitzada')], default='A', max_length=1)),
                ('any', models.IntegerField(default=aula.apps.sortides.models.return_any_actual)),
                ('acceptar_condicions', models.BooleanField(verbose_name='Accepto condicions de matrícula')),
                ('acceptacio_en', models.DateTimeField(null=True)),
                ('confirma_matricula', models.CharField(blank=True, choices=[('C', 'Confirma matrícula'), ('N', 'No confirma')], max_length=1, null=True, verbose_name='Confirmo matrícula')),
                ('curs_complet', models.BooleanField(default=False, help_text='Matrícula típica de totes les UFs', verbose_name='Matrícula del curs complet')),
                ('quantitat_ufs', models.IntegerField(blank=True, default=0, null=True, verbose_name='UFs soltes, curs no complet')),
                ('llistaufs', models.CharField(blank=True, help_text="En cas d'UFs soltes", max_length=250, null=True, verbose_name='Mòduls i ufs de la matrícula')),
                ('bonificacio', models.CharField(choices=[('0', 'Cap'), ('5', '50%'), ('1', '100%')], default='0', max_length=1, verbose_name='Tipus de bonificació taxes')),
                ('fracciona_taxes', models.BooleanField(default=False, verbose_name='Fracciona pagament taxes')),
                ('nom', models.CharField(default='', max_length=50, verbose_name='Nom alumne')),
                ('cognoms', models.CharField(default='', max_length=100, verbose_name='Cognoms alumne')),
                ('centre_de_procedencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Centre de procedència')),
                ('data_naixement', models.DateField(default=None, verbose_name='Data de naixement')),
                ('alumne_correu', models.EmailField(help_text="Correu de notificacions de l'alumne", max_length=254, null=True, verbose_name="Correu de l'alumne")),
                ('adreca', models.CharField(default='', max_length=250, verbose_name='Adreça')),
                ('localitat', models.CharField(default='', max_length=250, verbose_name='Localitat')),
                ('cp', models.CharField(default='', max_length=10, verbose_name='Codi postal')),
                ('rp1_nom', models.CharField(default='', max_length=250, verbose_name='Nom complet 1r responsable')),
                ('rp1_telefon', models.CharField(default='', max_length=15, verbose_name='Telèfon 1r responsable')),
                ('rp1_correu', models.EmailField(default='', max_length=254, verbose_name='Correu 1r responsable')),
                ('rp2_nom', models.CharField(blank=True, max_length=250, null=True, verbose_name='Nom complet 2n responsable')),
                ('rp2_telefon', models.CharField(blank=True, max_length=15, null=True, verbose_name='Telèfon 2n responsable')),
                ('rp2_correu', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correu 2n responsable')),
                ('alumne', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='matricula', to='alumnes.alumne')),
                ('curs', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='alumnes.curs', verbose_name='Curs on matricular-se')),
                ('preinscripcio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='extPreinscripcio.preinscripcio')),
                ('quota', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='sortides.quota')),
            ],
            options={
                'verbose_name': 'Matrícula',
                'verbose_name_plural': 'Matrícules',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fitxer', private_storage.fields.PrivateFileField(null=True, storage=private_storage.storage.files.PrivateFileSystemStorage(), upload_to='matricula/%Y/', verbose_name='Fitxer amb documents')),
                ('matricula', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='matricula.matricula')),
            ],
            options={
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documents',
            },
        ),
    ]
