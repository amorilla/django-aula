# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-09 17:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuaris', '0002_professorconserge'),
        ('incidencies', '0003_incidencia_gestionada_pel_tutor_motiu'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidencia',
            name='professional_inicia',
            field=models.ForeignKey(blank=True, help_text='Professor que inicialment posa la incid\xe8ncia per\xf2 que no la gestiona (ex: conserge)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incidencia_inicia_set', related_query_name='incidencia_inicia', to='usuaris.ProfessorConserge'),
        ),
        migrations.AlterField(
            model_name='incidencia',
            name='gestionada_pel_tutor',
            field=models.BooleanField(default=False, editable=False, help_text='Aquesta incid\xe8ncia podr\xe0 ser gestionada pel tutor.".', verbose_name='Incid\xe8ncia pot ser gestionada pel tutor'),
        ),
        migrations.AlterField(
            model_name='incidencia',
            name='gestionada_pel_tutor_motiu',
            field=models.CharField(choices=[('1AHora', 'Pot ser gestionada pel tutor: Retard de 1a hora'), ('ForaAula', "Pot ser gestionada pel tutor: Incid\xe8ncia fora d'aula"), ('Guardia', 'Pot ser gestionada pel tutor: Incid\xe8ncia en hora de Gu\xe0rdia'), ('N/A', 'Pot ser gestionada pel tutor')], default=b'', editable=False, max_length=20),
        ),
    ]
