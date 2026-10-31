"""背景工作共用的執行緒池（取代每個請求各開一條 threading.Thread）。

- run_light：搜尋統計、寄信等短工作
- run_heavy：下載 CSV、敏感資料檔案等長工作；同時最多 BG_HEAVY_WORKERS 個，其餘排隊

每個 gunicorn worker 各有一組池。工作結束一律關閉該執行緒的 DB 連線，例外記錄到 log。
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from django.db import connection

from conf.settings import env

logger = logging.getLogger(__name__)

_light = ThreadPoolExecutor(max_workers=env.int('BG_LIGHT_WORKERS', default=4), thread_name_prefix='bg-light')
_heavy = ThreadPoolExecutor(max_workers=env.int('BG_HEAVY_WORKERS', default=4), thread_name_prefix='bg-heavy')


def _run(func, args):
    try:
        func(*args)
    except Exception:
        logger.exception('background task failed: %s', getattr(func, '__name__', func))
    finally:
        connection.close()


def run_light(func, *args):
    _light.submit(_run, func, args)


def run_heavy(func, *args):
    _heavy.submit(_run, func, args)
