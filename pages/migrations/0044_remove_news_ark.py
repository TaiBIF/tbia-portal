# Generated by Django 4.0.4 on 2024-10-28 08:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0043_alter_news_ark'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='news',
            name='ark',
        ),
    ]
