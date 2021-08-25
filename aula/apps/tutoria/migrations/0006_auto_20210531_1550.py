# Generated by Django 3.1.6 on 2021-05-31 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoria', '0005_auto_20201109_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actuacio',
            name='assumpte',
            field=models.CharField(choices=[('T', 'Tutoria individualitzada'), ('C', 'A/I Conflicte comportament'), ('V', 'A/I Valoració'), ('S', 'A/I Seguiment'), ('O', 'A/I Orientació acadèmica'), ('E', 'A/I Suport educatiu'), ('G', 'A/I Gestió de les emocions'), ('I', 'A/I Gestió social'), ('P', 'A/I Pla individualitzat'), ('A', 'Actuació puntual')], help_text='Assumpte', max_length=1),
        ),
    ]
