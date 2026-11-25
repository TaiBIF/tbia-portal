# 7.1：資源頁（Resource）上的「資料欄位說明文件」「名錄欄位說明文件」PDF 改為連到欄位說明頁 /data-fields
# 預設只列出會改的資料；確認後加 -e APPLY=1 才寫入。測試站、正式站各跑一次（正式站在 8.1 部署後）
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/relink_field_docs.py
#   docker compose -f staging-v2.yml exec -T -e APPLY=1 web-v2 python manage.py shell < scripts/v2_migration/relink_field_docs.py
# 歷史版本（ResourceVersion）不動；有 ARK 的資源，ARK 之後會指到網頁
import os

from manager.models import Ark
from pages.models import Resource

APPLY = os.environ.get('APPLY') == '1'
TARGETS = [('資料欄位說明文件', 'occurrence-area'), ('名錄欄位說明文件', 'species-area')]

n = 0
for key, anchor in TARGETS:
    for r in Resource.objects.filter(url__icontains=key).order_by('id'):
        prefix = '/en-us' if r.lang == 'en-us' else ''
        new_url = f'{prefix}/data-fields#{anchor}'
        ark = Ark.objects.filter(type='resource', model_id=str(r.id)).values_list('ark', flat=True).first()
        print(f'id={r.id} | {r.title} | {r.lang} | {r.resource_type} | {r.url} → ext-link {new_url}' + (f' | ARK {ark}' if ark else ''))
        n += 1
        if APPLY:
            r.resource_type, r.extension, r.url = 'ext-link', 'link', new_url
            r.save(update_fields=['resource_type', 'extension', 'url'])

print(f'{"已更新" if APPLY else "將更新（加 -e APPLY=1 才寫入）"} {n} 筆')
