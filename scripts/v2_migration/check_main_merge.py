# 11/21 main 合入 v2 的檢查（API key 管理、change_manager_page 權限、XSS 修正）：測試站 portal-v2 用
# 用法（在 ~/tbia-portal-v2）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_main_merge.py > /tmp/check_main_merge.txt 2>&1
# 選項：-e MERGE_TEMP_KEY=1  暫時建一把「停用」與一把「通過」的 APIkey 測 v1 / v2 API，結束時刪除（會寫 portal-v2 DB）
# 不加選項時只讀不寫。每項印 PASS / FAIL / SKIP，編號對應交接文件「main 合入測試清單（11/21）」
import json
import os
import traceback
import uuid

from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.test import RequestFactory

from api.models import APIkey
from data.utils import create_query_display, query_a_href
from manager.models import User
import api.views as av
try:
    import api.v2 as v2   # 5.2 起才有；只合入整合分支、還沒合 5.2 時 M-3a / M-3c 略過
except ImportError:
    v2 = None
import manager.views as mv

RF = RequestFactory()
RESULTS = []
HOST = 'v2-wip.tbiadata.tw'


def report(no, ok, msg=''):
    status = {True: 'PASS', False: 'FAIL', None: 'SKIP'}[ok]
    RESULTS.append((no, status))
    print(f'[{status}] {no} {msg}')


def run(no, fn):
    try:
        fn()
    except Exception as e:
        report(no, False, f'例外：{e}')
        traceback.print_exc()


def c_1():
    qd = QueryDict('record_type=occ&recordedBy=<script>alert(1)</script>&name=A"B')
    web = create_query_display(qd)
    txt = create_query_display(qd, escape_values=False)
    report('M-1a', '<script>' not in web and '&lt;script&gt;' in web and '&quot;' in web,
           '搜尋條件顯示（網頁）跳脫使用者輸入')
    report('M-1b', '<script>alert(1)</script>' in txt and '&lt;' not in txt,
           '搜尋條件顯示（escape_values=False，報表用）維持純文字')
    qd = QueryDict('record_type=occ&is_protected=n&has_image=y')   # 舊字串：已停用條件仍要標示
    report('M-1c', '已停用' in create_query_display(qd), '已停用條件仍標示「已停用」（3.4 行為不變）')
    a = query_a_href('', '/search/occurrence?name="><script>x</script>')
    report('M-1d', '"><script>' not in a and '&quot;&gt;&lt;script&gt;' in a, '再次查詢連結網址跳脫')


def post(user, **data):
    req = RF.post('/change_manager_page', data, HTTP_HOST=HOST)
    req.user = user
    return mv.change_manager_page(req)


def c_2():
    req = RF.get('/change_manager_page', {'page': 1, 'menu': 'feedback'}, HTTP_HOST=HOST)
    req.user = AnonymousUser()
    report('M-2a', mv.change_manager_page(req).status_code == 405, 'GET 回 405')
    report('M-2b', post(AnonymousUser(), page=1, menu='feedback').status_code == 403, '未登入 POST 回 403')
    admin = User.objects.filter(is_system_admin=True, status='pass').first()
    normal = User.objects.filter(is_system_admin=False, is_partner_admin=False, status='pass').first()
    if not admin or not normal:
        report('M-2c', None, '找不到系統管理員或一般帳號')
        return
    report('M-2c', post(normal, page=1, menu='feedback').status_code == 403, '一般帳號查系統後台 feedback 回 403')
    report('M-2d', post(admin, page=1, menu='not-a-menu').status_code == 400, '不存在的 menu 回 400')
    r = post(admin, page='abc', menu='feedback')
    ok = r.status_code == 200 and json.loads(r.content).get('current_page') == 1
    report('M-2e', ok, 'page 亂帶（abc）以第 1 頁處理、不出錯')
    for menu in ('feedback', 'sensitive_track', 'news_apply', 'resource', 'qa', 'account', 'sensitive_apply'):
        r = post(admin, page=1, menu=menu)
        if r.status_code != 200:
            report('M-2f', False, f'系統管理員 menu={menu} 回 {r.status_code}')
            return
    report('M-2f', True, '系統管理員各 menu 分頁皆 200（含 v2 的再次查詢連結）')
    r = post(normal, page=1, menu='download')
    report('M-2g', r.status_code == 200, '一般帳號自己的下載紀錄 200')


def c_3():
    if os.environ.get('MERGE_TEMP_KEY') != '1':
        for n in ('M-3a', 'M-3b', 'M-3c'):
            report(n, None, '加 -e MERGE_TEMP_KEY=1 才檢查（會暫時建 APIkey）')
        return
    disabled = APIkey.objects.create(key='check-merge-' + uuid.uuid4().hex, status='disabled')
    ok_key = APIkey.objects.create(key='check-merge-' + uuid.uuid4().hex, status='pass')
    try:
        if v2:
            r = v2.occurrence(RF.get('/api/v2/occurrence', {'limit': 1, 'from_example': '1'}, HTTP_HOST=HOST,
                                     HTTP_AUTHORIZATION=f'Bearer {disabled.key}'))
            report('M-3a', r.status_code == 401, f'停用的金鑰打 v2 API 回 {r.status_code}（應 401）')
        else:
            report('M-3a', None, '還沒有 api/v2.py（5.2 未合入）')
        r = av.occurrence(RF.get('/api/v1/occurrence', {'limit': 1, 'apikey': disabled.key, 'from_example': '1'},
                                 HTTP_HOST=HOST))
        code = json.loads(r.content).get('status', {}).get('code')
        report('M-3b', code == 400, f'停用的金鑰打 v1 API status.code={code}（應 400，v1 行為不變）')
        if v2:
            r = v2.occurrence(RF.get('/api/v2/occurrence', {'limit': 1, 'from_example': '1'}, HTTP_HOST=HOST,
                                     HTTP_AUTHORIZATION=f'Bearer {ok_key.key}'))
            report('M-3c', r.status_code == 200, f'通過的金鑰打 v2 API 回 {r.status_code}')
        else:
            report('M-3c', None, '還沒有 api/v2.py（5.2 未合入）')
    finally:
        APIkey.objects.filter(id__in=[disabled.id, ok_key.id]).delete()


run('M-1', c_1)
run('M-2', c_2)
run('M-3', c_3)
counts = {}
for _, s in RESULTS:
    counts[s] = counts.get(s, 0) + 1
print('合計：' + '、'.join(f'{k} {v}' for k, v in sorted(counts.items())))
