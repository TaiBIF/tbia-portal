# Generated by Django 3.2.10 on 2022-09-23 08:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0018_partner_info'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partner',
            name='description',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='image',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='link',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='logo',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='subtitle',
        ),
    ]