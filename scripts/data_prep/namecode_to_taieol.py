from data.models import Namecode
import requests


for n in Namecode.objects.all():
    if n.namecode:
        print(n.namecode)
        url = 'https://data.taieol.tw/eol/endpoint/taxondesc/species/{}'.format(n.namecode)
        r = requests.get(url)
        data = r.json()
        if data:
            if data.get('tid'):
                n.taieol_id = data.get('tid')
                n.save()
