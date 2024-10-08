# Generated by Django 3.2.10 on 2022-09-21 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0012_user_first_login'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        migrations.AddField(
            model_name='user',
            name='is_partner_account',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_partner_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_system_admin',
            field=models.BooleanField(default=False),
        ),
    ]
