# CKEDITOR filename generation

def get_filename(filename, request):
    return filename.upper()

notif_map = {
    0: '/manager?menu=download_taxon',
    1: '/manager?menu=download',
    4: '/manager?menu=sensitive',
    6: '/manager',
    7: '/manager/system/news?menu=list',
    8: '/manager/partner/news?menu=news'
  }

from conf.settings import env

web_mode = env('ENV')
if web_mode == 'stag':
    scheme = 'https'
elif web_mode == 'prod':
    scheme = 'https'
else:
    scheme = 'http'
