# Generated by Django 3.2.5 on 2021-07-26 01:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('alumnes', '0015_auto_20210726_0121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Preinscripcio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nom')),
                ('cognoms', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cognoms')),
                ('ralc', models.CharField(blank=True, max_length=20, null=True, verbose_name='Identificació RALC')),
                ('codiestudis', models.CharField(blank=True, max_length=50, null=True, verbose_name='Codi ensenyament')),
                ('nomestudis', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nom ensenyament')),
                ('codimodalitat', models.CharField(blank=True, max_length=50, null=True, verbose_name='Codi modalitat')),
                ('nommodalitat', models.CharField(blank=True, max_length=100, null=True, verbose_name='Modalitat')),
                ('curs', models.CharField(blank=True, max_length=50, null=True, verbose_name='Curs')),
                ('regim', models.CharField(blank=True, max_length=50, null=True, verbose_name='Règim')),
                ('torn', models.CharField(blank=True, max_length=50, null=True, verbose_name='Torn')),
                ('identificador', models.CharField(blank=True, max_length=50, null=True, verbose_name='DNI-NIE-PASS')),
                ('tis', models.CharField(blank=True, max_length=50, null=True, verbose_name='TIS')),
                ('naixement', models.DateField(blank=True, null=True, verbose_name='Data naixement')),
                ('sexe', models.CharField(blank=True, max_length=10, null=True, verbose_name='Sexe')),
                ('nacionalitat', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nacionalitat')),
                ('paisnaixement', models.CharField(blank=True, max_length=100, null=True, verbose_name='País naixement')),
                ('adreça', models.CharField(blank=True, max_length=300, null=True, verbose_name='Adreça')),
                ('provincia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Província residència')),
                ('municipi', models.CharField(blank=True, max_length=100, null=True, verbose_name='Municipi residència')),
                ('localitat', models.CharField(blank=True, max_length=100, null=True, verbose_name='Localitat residència')),
                ('cp', models.CharField(blank=True, max_length=50, null=True, verbose_name='CP')),
                ('paisresidencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='País residència')),
                ('telefon', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telèfon')),
                ('correu', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correu electrònic')),
                ('tdoctut1', models.CharField(blank=True, max_length=50, null=True, verbose_name='Tipus doc. tutor 1')),
                ('doctut1', models.CharField(blank=True, max_length=50, null=True, verbose_name='Núm. doc. tutor 1')),
                ('nomtut1', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nom tutor 1')),
                ('cognomstut1', models.CharField(blank=True, max_length=1000, null=True, verbose_name='Cognoms tutor 1')),
                ('tdoctut2', models.CharField(blank=True, max_length=50, null=True, verbose_name='Tipus doc. tutor 2')),
                ('doctut2', models.CharField(blank=True, max_length=50, null=True, verbose_name='Núm. doc. tutor 2')),
                ('nomtut2', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nom tutor 2')),
                ('cognomstut2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cognoms tutor 2')),
                ('codicentreprocedencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Codi centre proc.')),
                ('centreprocedencia', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nom centre proc.')),
                ('codiestudisprocedencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Codi ensenyament proc.')),
                ('estudisprocedencia', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nom ensenyament proc.')),
                ('cursestudisprocedencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Curs proc.')),
                ('centreassignat', models.CharField(blank=True, max_length=50, null=True, verbose_name='Centre assignat')),
                ('estat', models.CharField(blank=True, max_length=50, null=True, verbose_name='Estat sol·licitud')),
                ('any', models.IntegerField(verbose_name='Any')),
            ],
            options={
                'ordering': ['codiestudis', 'cognoms', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='Nivell2Aula',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivellgedac', models.CharField(blank=True, max_length=60, unique=True)),
                ('nivellDjau', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='nivell2djau_set', to='alumnes.nivell')),
            ],
            options={
                'verbose_name': 'Mapeig Nivell Aula Gedac',
                'verbose_name_plural': 'Mapejos Nivells Aula Gedac',
                'ordering': ['nivellDjau', 'nivellgedac'],
            },
        ),
    ]
