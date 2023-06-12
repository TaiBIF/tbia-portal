# CKEDITOR filename generation

def get_filename(filename, request):
    return filename.upper()

notif_map = {
    0: '/manager?menu=download_taxon',
    1: '/manager?menu=download',
    4: '/manager?menu=sensitive',
    6: '/manager',
    7: '/manager/system/news?menu=list',
    8: '/manager/partner/news?menu=list'
  }
