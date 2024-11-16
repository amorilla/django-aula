# Generated by Django 5.0.9 on 2024-11-09 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alumnes', '0018_alumne_usuaris_app_associats'),
        ('missatgeria', '0003_auto_20190331_1541'),
        ('presencia', '0012_rename_presencia_controlassiste_alumne_id_estat_id_relac_8957bdde_idx_presencia_c_alumne__6961f9_idx'),
        ('usuaris', '0014_notifusuari'),
    ]

    operations = [
        migrations.AddField(
            model_name='controlassistencia',
            name='moment',
            field=models.DateTimeField(null=True),
        ),
        migrations.RemoveIndex(
            model_name='controlassistencia',
            name='presencia_c_alumne__6961f9_idx',
        ),
        migrations.AddIndex(
            model_name='controlassistencia',
            index=models.Index(fields=['alumne', 'estat', 'moment'], name='presencia_c_alumne__b96483_idx'),
        ),
    ]
