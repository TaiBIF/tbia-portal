from manager.models import Partner


def get_partners(request):
    return {
       'partners': Partner.objects.all(),
    }
