# Generated by Django 3.2.10 on 2022-09-22 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0015_alter_user_partner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status'),
        ),
    ]