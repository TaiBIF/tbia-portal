"""背景工作。

- run_light：搜尋統計、寄信等短工作，用 web 程序內的執行緒池（掉了影響不大）
- run_heavy：下載 CSV、敏感資料檔案等長工作，寫進 django-q2 佇列（PostgreSQL），
  由獨立的 worker 容器（python manage.py run_worker）執行。web 重啟不影響；
  worker 中途被中斷時，工作會在 worker 重啟時（或 Q_CLUSTER['retry'] 秒後）重新派送，因此工作函式需可重複執行。
- 失敗（含逾時）由 on_task_failed 處理：只寄信通知系統管理員，使用者端維持「處理中」、不另行通知；
  管理員在 /admin/django_q/failure/ 用「Resubmit selected tasks to queue」重新產出後，使用者照常收到完成通知。

run_heavy 的參數會被 pickle 存進資料庫，請只傳基本型別（str / int / dict / list），
函式以 'app.module.func' 字串或模組層級函式傳入。
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from django.db import connection, transaction
from django.utils.module_loading import import_string

from conf.settings import env

logger = logging.getLogger(__name__)

_light = ThreadPoolExecutor(max_workers=env.int('BG_LIGHT_WORKERS', default=4), thread_name_prefix='bg-light')

# 在 qcluster worker 程序內執行時為 True：run_light 直接同步執行，避免 worker 回收時丟掉寄信
_in_worker = False


def _run(func, args):
    try:
        func(*args)
    except Exception:
        logger.exception('background task failed: %s', getattr(func, '__name__', func))
    finally:
        connection.close()


def run_light(func, *args):
    if _in_worker:
        try:
            func(*args)
        except Exception:
            logger.exception('background task failed: %s', getattr(func, '__name__', func))
        return
    _light.submit(_run, func, args)


def _func_path(func):
    if isinstance(func, str):
        return func
    return f'{func.__module__}.{func.__qualname__}'


FAIL_HOOK = 'conf.background.on_task_failed'


def run_heavy(func, *args, query_id=None):
    """把工作排進佇列。

    query_id：使用者的下載／申請編號，失敗通知信會附上對應的檔案編號與使用者。
    工作失敗（含逾時）時只通知系統管理員，SearchQuery 維持 pending（使用者端顯示「處理中」）。
    """
    from django_q.tasks import async_task

    func_path = _func_path(func)
    q_options = {'task_name': f"{func_path.rsplit('.', 1)[-1]}:{query_id or ''}", 'hook': FAIL_HOOK}
    # 等目前的 transaction commit 後才排入，避免 worker 讀不到剛建立的資料
    transaction.on_commit(lambda: async_task('conf.background.execute', func_path, list(args), query_id,
                                             q_options=q_options))


def execute(func_path, args, query_id=None):
    """worker 端的實際進入點。"""
    global _in_worker
    _in_worker = True
    import_string(func_path)(*args)


# ---------------- 失敗處理 ----------------

def on_task_failed(task):
    """django-q2 hook（成功與失敗都會呼叫）：失敗時只通知系統管理員。

    使用者端維持「處理中」、不寄失敗通知；管理員重新送出成功後，使用者照常收到下載完成通知。
    """
    if task.success:
        return
    global _in_worker
    _in_worker = True  # 在 qcluster 程序內，寄信直接同步執行

    args = task.args or []
    func_path = args[0] if args else str(task.func)
    query_id = args[2] if len(args) > 2 else None
    logger.error('background task %s failed (query_id=%s)', task.name, query_id)

    sq = None
    if query_id:
        from manager.models import SearchQuery
        sq = SearchQuery.objects.filter(query_id=query_id).select_related('user').first()
    try:
        notify_admins_task_failed(task, func_path, sq)
    except Exception:
        logger.exception('notify admins failed')


def notify_admins_task_failed(task, func_path, sq=None):
    from django.utils.html import escape
    from manager.models import User
    from manager.views import send_notification
    from conf.utils import scheme

    admin_ids = list(User.objects.filter(is_system_admin=True).values_list('id', flat=True))
    if not admin_ids:
        return
    host = env('PORTAL_HOST', default='')
    result = str(task.result or '')
    args = task.args or []
    params = repr(args[1]) if len(args) > 1 else ''
    content = f"背景工作執行失敗，請確認原因後至後台重新送出。<br><br><b>工作：</b>{escape(func_path)}"
    if sq:
        content += (f"<br><b>檔案編號：</b>{escape(sq.query_id)}（{escape(sq.type)} #{sq.personal_id}）"
                    f"<br><b>使用者：</b>{escape(sq.user.email)}（使用者端仍顯示「處理中」，未收到失敗通知）")
    content += f"<br><b>參數：</b>{escape(params[:500])}"
    content += f"<br><b>錯誤：</b><pre style=\"white-space:pre-wrap\">{escape(result[-2000:])}</pre>"
    content += (f"<b>重新產出：</b>至 {scheme}://{host}/admin/django_q/failure/ 勾選此筆，"
                f"執行「Resubmit selected tasks to queue」；完成後使用者會照常收到下載連結。")
    send_notification(admin_ids, content, '背景工作執行失敗通知')
