from datetime import timedelta
from manager.models import Partner
from django.utils import timezone


def get_partners(request):
    return {
       # 個人後台選擇所屬夥伴單位 / 意見回饋選擇回饋對象
       'partners': Partner.objects.all().order_by('title'),
    }


def get_index_partners(request):
    # 回傳首頁上顯示的正式會員
    # 排除中研院博物館&昆標館
    return {
       'index_partners': Partner.objects.filter(is_collaboration=False).values('abbreviation','title',"title_en",'logo','id','index_order').distinct("title","title_en","index_order").order_by('index_order'),
    }


def get_index_collaborates(request):
    # 回傳首頁上顯示的合作夥伴
    # 排除中研院博物館&昆標館
    return {
       'index_collaborates': Partner.objects.filter(is_collaboration=True).values('abbreviation','title',"title_en",'logo','id','index_order').distinct("title","title_en","index_order").order_by('index_order'),
    }


def today(request):
   today = timezone.now()+timedelta(hours=8)
   return {
       'today': today.strftime('%Y/%m/%d'),
    }
