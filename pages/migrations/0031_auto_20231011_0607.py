# Generated by Django 3.2.10 on 2023-10-11 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0030_qa_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(blank=True, choices=[(0, '下載名錄編號 #0000 已處理完成，請至後台查看'), (1, '下載資料編號 #0000 已處理完成，請至後台查看'), (2, '有新的意見回饋 #0000，請至後台查看'), (3, '有新的單次使用敏感資料申請 #0000，請至後台審核'), (4, '單次使用敏感資料申請編號 #0000 審核已完成，請至後台查看'), (5, '有新的單位帳號 #0000 申請，請至後台審核'), (6, '申請單位帳號審核已完成，結果為：0000'), (7, '有新的消息 #0000 發布申請，請至後台審核'), (8, '消息 #0000 發布審核已完成，請至後台查看')], null=True),
        ),
        migrations.DeleteModel(
            name='Download',
        ),
    ]