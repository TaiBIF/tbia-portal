# 步驟 4.4：歷史統計的來源資料庫名稱改成 v2 sourceDatabase（舊 rightsHolder → 新名稱，8 筆）
# 範圍：
#   - DataStat、UserDownloadStat、TaxonStat（含 taiwan_percentage）、MatchStat、MatchReport 的 rights_holder
#   - SearchStat.stat、SearchQuery.stat / sensitive_stat 的 JSON val（夥伴敏感資料報表與下載紀錄筆數以名稱比對）
#   - TAXON_STAT_DIR 底下 {舊名稱}_{類群}.csv 改名（新名稱檔已存在就不動）
# 同一筆統計新舊名稱都有時（例：stat_taxon 已寫入新名稱的 taiwan_percentage、monthly_stat 重跑的月份），保留新名稱那筆、刪掉舊的；
# JSON 內新舊名稱並存時筆數相加。
# 正式站於 8.1 ② 與 0098 一起 migrate（先備份 portal DB）；測試站 portal-v2 可提前執行。
# 退回（backwards）只把名稱改回舊名稱，合併 / 刪除的列不會還原，要完整還原請用備份。
# SearchQuery / SearchStat 的 query 字串不在此處理（讀取時轉換，4.2；一次轉換見 P2-7）。

import os

from django.conf import settings
from django.db import migrations
from django.db.models import Q


SOURCE_DATABASE_RENAME = {
    '中央研究院生物多樣性中心動物標本館': '中央研究院動物標本館 ASIZ',
    '中央研究院生物多樣性中心植物標本資料庫': '中央研究院植物標本館 HAST',
    '國家海洋資料庫及共享平台': '國家海洋資料庫及共享平臺',
    '國立海洋生物博物館生物典藏管理系統': '生物典藏管理系統',
    '科博典藏 (NMNS Collection)': '科博典藏',
    '國立臺灣博物館典藏': '國立臺灣博物館生物典藏資料',
    '愛自然-臺灣(iNaturalist Taiwan)': '愛自然-臺灣',
    '中油生態地圖': '中油生態保育資料庫',
}

# 每個 model 判斷「同一筆統計」的欄位（不含 rights_holder）；None = 不去重，直接改名
STAT_KEYS = {
    'DataStat': ['type', 'year_month'],
    'UserDownloadStat': ['type', 'option', 'year_month'],
    'TaxonStat': ['type', 'year', 'month', 'name'],
    'MatchStat': None,
    'MatchReport': None,
}
JSON_FIELDS = {
    'SearchStat': ['stat'],
    'SearchQuery': ['stat', 'sensitive_stat'],
}


def _rename_stats(apps, mapping, dedup=True):
    for model_name, keys in STAT_KEYS.items():
        Model = apps.get_model('manager', model_name)
        for old, new in mapping.items():
            old_qs = Model.objects.filter(rights_holder=old)
            if not old_qs.exists():
                continue
            if keys and dedup:
                existing = set(Model.objects.filter(rights_holder=new).values_list(*keys))
                dup_ids = [row[0] for row in old_qs.values_list('id', *keys) if tuple(row[1:]) in existing]
                if dup_ids:
                    Model.objects.filter(id__in=dup_ids).delete()
            old_qs.update(rights_holder=new)


def _merge_vals(items, mapping):
    """[{val, count}, ...] 的 val 依 mapping 改名，改名後重複的 val 筆數相加；回傳 (新 list, 是否有變)"""
    if not isinstance(items, list):
        return items, False
    out, index, changed = [], {}, False
    for item in items:
        if not isinstance(item, dict) or 'val' not in item:
            out.append(item)
            continue
        val = mapping.get(item['val'], item['val'])
        if val != item['val']:
            changed = True
        if val in index:
            merged = out[index[val]]
            try:
                merged['count'] = merged.get('count', 0) + item.get('count', 0)
            except TypeError:
                pass
            changed = True
            continue
        index[val] = len(out)
        out.append({**item, 'val': val})
    return out, changed


def _rename_json(apps, schema_editor, mapping):
    use_contains = schema_editor.connection.vendor == 'postgresql'
    for model_name, fields in JSON_FIELDS.items():
        Model = apps.get_model('manager', model_name)
        qs = Model.objects.all()
        if use_contains:   # jsonb @>：只取含舊名稱的列，不掃整張表的 JSON
            cond = Q()
            for f in fields:
                for old in mapping:
                    cond |= Q(**{f'{f}__contains': [{'val': old}]})
            qs = qs.filter(cond)
        batch = []
        for obj in qs.only('id', *fields).iterator(chunk_size=2000):
            dirty = False
            for f in fields:
                new_val, changed = _merge_vals(getattr(obj, f), mapping)
                if changed:
                    setattr(obj, f, new_val)
                    dirty = True
            if dirty:
                batch.append(obj)
            if len(batch) >= 1000:
                Model.objects.bulk_update(batch, fields)
                batch = []
        if batch:
            Model.objects.bulk_update(batch, fields)


def _rename_csv(mapping):
    stat_dir = getattr(settings, 'TAXON_STAT_DIR', None)
    if not stat_dir or not os.path.isdir(stat_dir):
        return
    for fname in os.listdir(stat_dir):
        for old, new in mapping.items():
            if fname.startswith(f'{old}_') and fname.endswith('.csv'):
                target = os.path.join(stat_dir, new + fname[len(old):])
                if not os.path.exists(target):
                    os.rename(os.path.join(stat_dir, fname), target)


def forwards(apps, schema_editor):
    _rename_stats(apps, SOURCE_DATABASE_RENAME)
    _rename_json(apps, schema_editor, SOURCE_DATABASE_RENAME)
    _rename_csv(SOURCE_DATABASE_RENAME)


def backwards(apps, schema_editor):
    reverse = {v: k for k, v in SOURCE_DATABASE_RENAME.items()}
    _rename_stats(apps, reverse, dedup=False)
    _rename_json(apps, schema_editor, reverse)


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0098_partner_dbname_v2'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
