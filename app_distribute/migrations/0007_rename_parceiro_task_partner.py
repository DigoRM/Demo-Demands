# Generated by Django 3.2.18 on 2023-03-02 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_distribute', '0006_parceiro'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='parceiro',
            new_name='partner',
        ),
    ]
