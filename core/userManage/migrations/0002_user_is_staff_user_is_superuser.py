# Generated by Django 5.2 on 2025-04-09 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userManage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False),
        ),
    ]
