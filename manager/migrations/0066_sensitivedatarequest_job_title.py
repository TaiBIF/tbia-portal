# Generated by Django 4.0.4 on 2024-05-21 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0065_alter_datastat_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensitivedatarequest',
            name='job_title',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
