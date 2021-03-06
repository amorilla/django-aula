# Generated by Django 3.0.6 on 2020-07-01 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sortides', '0027_pagament_datalimit'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipusQuota',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Tipus de quota',
                'verbose_name_plural': 'Tipus de quotes',
                'ordering': ['nom'],
            },
        ),
        migrations.RemoveField(
            model_name='quota',
            name='es_taxa',
        ),
        migrations.AddField(
            model_name='quota',
            name='tipus',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='sortides.TipusQuota'),
        ),
    ]
