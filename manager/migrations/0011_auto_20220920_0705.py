# Generated by Django 3.2.10 on 2022-09-20 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0010_auto_20220920_0652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=True),
        ),
    ]