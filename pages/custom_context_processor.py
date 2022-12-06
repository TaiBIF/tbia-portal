from datetime import timedelta
from manager.models import Partner
from django.utils import timezone


def get_partners(request):
    return {
       'partners': Partner.objects.all().order_by('title'),
    }


def get_index_partners(request):
    # 回傳首頁上顯示的夥伴單位
    # 排除城鄉分署&中研院博物館
    return {
       'index_partners': Partner.objects.exclude(group__in=['brmas','tcd']).order_by('id'),
    }


def today(request):
   today = timezone.now()+timedelta(hours=8)
   return {
       'today': today.strftime('%Y/%m/%d'),
    }
