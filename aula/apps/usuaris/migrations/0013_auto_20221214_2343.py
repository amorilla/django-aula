# Generated by Django 3.2.16 on 2022-12-14 23:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('alumnes', '0018_alumne_usuaris_app_associats'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('usuaris', '0012_auto_20221214_2306'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='qrportal',
            name='abstractqrportal_ptr',
        ),
        migrations.AddField(
            model_name='qrportal',
            name='alumne_referenciat',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='qr_portal_set', related_query_name='qr_portal', to='alumnes.alumne'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='qrportal',
            name='clau',
            field=models.CharField(db_index=True, default=None, max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='qrportal',
            name='darrera_sincronitzacio',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qrportal',
            name='es_el_token_actiu',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qrportal',
            name='id',
            field=models.AutoField(auto_created=True, default=django.utils.timezone.now, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='qrportal',
            name='localitzador',
            field=models.CharField(db_index=True, default='-', max_length=4, unique=True),
        ),
        migrations.AddField(
            model_name='qrportal',
            name='moment_captura',
            field=models.DateTimeField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='qrportal',
            name='moment_confirmat_pel_tutor',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qrportal',
            name='moment_expedicio',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='qrportal',
            name='novetats_detectades_moment',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qrportal',
            name='usuari_referenciat',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='AbstractQRPortal',
        ),
    ]
