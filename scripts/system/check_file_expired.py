from manager.models import SearchQuery
from datetime import datetime, tzinfo,timedelta
import pandas as pd
import os
from pathlib import Path

# 從manager_searchquery撈modified > 三個月 & status != 'fail' 的檔案
# 若超過三個月 -> 刪除 & status改存expired

exp = datetime.now() - timedelta(days=63)

for sq in SearchQuery.objects.filter(modified__lt=exp).exclude(status='fail'):
    sq.status = 'expired'
    filename = sq.query_id
    type = sq.type
    sq.save()


# 緩衝三天再刪除檔案 
exp = datetime.now() - timedelta(days=66)
# 如果更新日期 比過期的日期還小(早)的話 代表已過期

for sq in SearchQuery.objects.filter(modified__lt=exp, status='expired'):
    path = f'/tbia-volumes/media/download/{sq.type}/tbia_{ sq.query_id }.zip'
    my_file = Path(path)
    my_file.unlink(missing_ok=True)