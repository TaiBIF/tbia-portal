from manager.models import SearchQuery
from datetime import datetime, tzinfo,timedelta
import pandas as pd
import os
from pathlib import Path

# 從manager_searchquery撈modified > 一年 & status != 'fail' 的檔案
# 若超過一年 -> 刪除 & status改存expired

exp = datetime.now() - timedelta(days=365)

for sq in SearchQuery.objects.filter(modified__lt=exp).exclude(status='fail'):
    sq.status = 'expired'
    filename = sq.query_id
    type = sq.type
    path = f'/media/download/{sq.type}/{sq.user_id}_{ sq.query_id }.csv'
    my_file = Path(path)
    my_file.unlink(missing_ok=True)
    sq.save()
