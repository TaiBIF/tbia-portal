# Generated by Django 3.2.10 on 2023-11-16 02:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0046_alter_workday_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='about',
            name='content_en',
            field=models.TextField(blank=True, null=True),
        ),
    ]
