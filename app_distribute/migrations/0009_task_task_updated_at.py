# Generated by Django 3.2.18 on 2023-03-03 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_distribute', '0008_task_parceiro'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='task_updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
