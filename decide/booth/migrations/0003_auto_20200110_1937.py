# Generated by Django 2.0 on 2020-01-10 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booth', '0002_auto_20200110_1927'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='municipio',
            field=models.CharField(default=None, max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='sexo',
            field=models.CharField(default=None, max_length=10),
        ),
    ]
