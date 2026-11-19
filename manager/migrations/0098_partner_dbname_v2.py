# 步驟 2.1 / 8.1 ②：Partner.info[].dbname 改成 v2 sourceDatabase 名稱（11/12 定案的 8 筆，見 data/search_params.py SOURCE_DATABASE_RENAME）
# - 正式站不可在切換前執行：v1 的 dbname 必須等於資料中的 rightsHolder（8.1 ② 與 0099 一起 migrate，先備份 portal DB）
# - cpc 的 dbname 線上是「觀塘生態保育網」（與 v1 資料的「中油生態地圖」不同），兩個舊值都改成新名稱
# - 對照表複製一份在這裡（migration 不 import 程式碼，之後改程式不影響這個 migration）
# - 只改名稱不同的 dbname，其他 info 欄位不動；重跑不會重複改

from django.db import migrations


DBNAME_RENAME = {
    '中央研究院生物多樣性中心動物標本館': '中央研究院動物標本館 ASIZ',
    '中央研究院生物多樣性中心植物標本資料庫': '中央研究院植物標本館 HAST',
    '國家海洋資料庫及共享平台': '國家海洋資料庫及共享平臺',
    '國立海洋生物博物館生物典藏管理系統': '生物典藏管理系統',
    '科博典藏 (NMNS Collection)': '科博典藏',
    '國立臺灣博物館典藏': '國立臺灣博物館生物典藏資料',
    '愛自然-臺灣(iNaturalist Taiwan)': '愛自然-臺灣',
    '中油生態地圖': '中油生態保育資料庫',
    '觀塘生態保育網': '中油生態保育資料庫',
}
# 退回時 cpc 回到 v1 資料用的名稱
DBNAME_REVERSE = {v: k for k, v in DBNAME_RENAME.items() if k != '觀塘生態保育網'}


def _rename(apps, mapping):
    Partner = apps.get_model('manager', 'Partner')
    for p in Partner.objects.all().order_by('id'):
        changed = False
        for info in (p.info or []):
            new = mapping.get(info.get('dbname'))
            if new:
                info['dbname'] = new
                changed = True
        if changed:
            p.save(update_fields=['info'])


def forwards(apps, schema_editor):
    _rename(apps, DBNAME_RENAME)


def backwards(apps, schema_editor):
    _rename(apps, DBNAME_REVERSE)


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0097_partner_tbia_partner_id_data'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
