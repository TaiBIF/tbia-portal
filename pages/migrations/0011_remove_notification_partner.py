# Generated by Django 3.2.10 on 2022-10-05 02:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0010_auto_20221003_0300'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='partner',
        ),
    ]