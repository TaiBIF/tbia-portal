# Generated by Django 4.0.4 on 2023-12-01 04:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0047_about_content_en'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='breadtitle_en',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='partner',
            name='select_title_en',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='partner',
            name='title_en',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
