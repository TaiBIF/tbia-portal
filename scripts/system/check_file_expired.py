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
    path = f'/media/download/{sq.type}/tbia_{ sq.query_id }.zip'
    my_file = Path(path)
    my_file.unlink(missing_ok=True)
    sq.save()
