# Generated by Django 3.0.6 on 2020-07-01 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sortides', '0028_auto_20200701_1845'),
        ('alumnes', '0012_nivell_matricula_oberta'),
    ]

    operations = [
        migrations.AddField(
            model_name='nivell',
            name='taxes',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='sortides.TipusQuota'),
        ),
    ]
