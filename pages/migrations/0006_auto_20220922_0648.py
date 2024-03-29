# Generated by Django 3.2.10 on 2022-09-22 06:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0005_auto_20220118_0719'),
    ]

    operations = [
        migrations.RenameField(
            model_name='download',
            old_name='partner_id',
            new_name='partner',
        ),
        migrations.RenameField(
            model_name='download',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='feedback',
            old_name='partner_id',
            new_name='partner',
        ),
        migrations.RenameField(
            model_name='news',
            old_name='partner_id',
            new_name='partner',
        ),
        migrations.RenameField(
            model_name='news',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='partner_id',
            new_name='partner',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='resource',
            old_name='partner_id',
            new_name='partner',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='user_id',
        ),
        migrations.AddField(
            model_name='resource',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
