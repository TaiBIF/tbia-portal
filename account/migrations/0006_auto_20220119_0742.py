# Generated by Django 3.2.10 on 2022-01-19 07:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_auto_20220119_0655'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partner',
            old_name='title',
            new_name='breadtitle',
        ),
        migrations.RenameField(
            model_name='partner',
            old_name='content',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='partner',
            old_name='db_name',
            new_name='subtitle',
        ),
    ]