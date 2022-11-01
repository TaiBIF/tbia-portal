from datetime import timedelta
from manager.models import Partner
from django.utils import timezone


def get_partners(request):
    return {
       'partners': Partner.objects.all(),
    }


def today(request):
   today = timezone.now()+timedelta(hours=8)
   return {
       'today': today.strftime('%Y/%m/%d'),
    }
