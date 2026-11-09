# 步驟 1.4：既有 Partner 補 tbia_partner_id（D2、D28）
# - ID = uuid5(固定命名空間, title)：各環境算出相同的值，title 相同的列自然共用；title 為空的列各自一個隨機 ID；group=gbif 留空
# - 命名空間與 manager/models.py 的 TBIA_PARTNER_ID_NAMESPACE 相同（migration 不 import models，故複製一份）
# - 只補還沒有 ID 的列，重跑不會改掉已產生的 ID
# - cpc dbname 是否改為「中油生態地圖」待確認，不在此 migration 處理

import uuid

from django.db import migrations


TBIA_PARTNER_ID_NAMESPACE = uuid.UUID('d758a377-ad4e-4933-a135-2145f1abedac')


def forwards(apps, schema_editor):
    Partner = apps.get_model('manager', 'Partner')
    for p in Partner.objects.filter(tbia_partner_id__isnull=True).order_by('id'):
        if p.group == 'gbif':
            continue
        pid = uuid.uuid5(TBIA_PARTNER_ID_NAMESPACE, p.title) if p.title else uuid.uuid4()
        p.tbia_partner_id = pid
        p.save(update_fields=['tbia_partner_id'])


def backwards(apps, schema_editor):
    Partner = apps.get_model('manager', 'Partner')
    Partner.objects.update(tbia_partner_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0096_partner_tbia_partner_id'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]