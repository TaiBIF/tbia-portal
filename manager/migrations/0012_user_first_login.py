# Generated by Django 3.2.10 on 2022-09-20 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0011_auto_20220920_0705'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='first_login',
            field=models.BooleanField(default=True),
        ),
    ]