from conf import settings

def turnstile(request):
    return {'TURNSTILE_SITE_KEY': settings.TURNSTILE_SITE_KEY}


def stat_urls(request):
    """後台 / 資料概況的統計檔下載連結（開發期指向 *_v2 目錄，見 settings）"""
    return {'TAXON_STAT_URL': settings.TAXON_STAT_URL, 'SEARCH_STAT_URL': settings.SEARCH_STAT_URL}
