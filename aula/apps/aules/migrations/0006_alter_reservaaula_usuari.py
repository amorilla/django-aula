# Generated by Django 3.2.7 on 2021-09-11 17:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('aules', '0005_auto_20190330_2012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservaaula',
            name='usuari',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]