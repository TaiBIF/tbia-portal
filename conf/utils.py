from conf.settings import env

notif_map = {
    0: '/manager?menu=download_taxon',
    1: '/manager?menu=download',
    4: '/manager?menu=sensitive',
    6: '/manager',
    7: '/manager/system/news?menu=news_apply',
    8: '/manager/partner/news?menu=news'
  }

web_mode = env('ENV')
if web_mode == 'stag':
    scheme = 'https'
elif web_mode == 'prod':
    scheme = 'https'
else:
    scheme = 'http'
