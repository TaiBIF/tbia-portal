from datetime import timedelta
from manager.models import Partner
from django.utils import timezone


def get_partners(request):
    return {
       'partners': Partner.objects.all().order_by('title'),
    }


def get_index_partners(request):
    # 回傳首頁上顯示的夥伴單位
    # 排除中研院博物館&昆標館
    return {
       'index_partners': Partner.objects.values('abbreviation','title',"title_en",'logo','id','index_order').distinct("title","title_en","index_order").order_by('index_order'),
    }


def today(request):
   today = timezone.now()+timedelta(hours=8)
   return {
       'today': today.strftime('%Y/%m/%d'),
    }
