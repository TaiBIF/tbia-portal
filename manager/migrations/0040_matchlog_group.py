# Generated by Django 3.2.10 on 2023-04-17 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0039_alter_matchlog_sourcescientificname'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchlog',
            name='group',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
