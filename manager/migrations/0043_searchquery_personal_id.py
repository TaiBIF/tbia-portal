# Generated by Django 3.2.10 on 2023-06-26 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0042_auto_20230523_0336'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchquery',
            name='personal_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]