# Generated by Django 3.2.10 on 2023-11-07 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0045_workday'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workday',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
    ]