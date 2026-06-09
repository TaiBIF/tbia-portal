import json
import requests

from django.core.management.base import BaseCommand

from conf.settings import SOLR_PREFIX
from manager.models import DataStat
from data.utils import rights_holder_map


class Command(BaseCommand):
    help = '統計各 rightsHolder 的資料筆數並寫入 DataStat'

    def add_arguments(self, parser):
        parser.add_argument('year_month', help='YYYY-MM, 例如 2026-03')

    def handle(self, *args, **options):
        year_month = options['year_month']

        query = {
            "query": "*:*",
            "offset": 0,
            "limit": 0,
            "facet": {
                "stat_rightsHolder": {
                    "type": "terms",
                    "field": "rightsHolder",
                    "mincount": 1,
                    "limit": -1,
                    "allBuckets": False,
                    "numBuckets": False,
                }
            },
        }

        resp = requests.post(
            f'{SOLR_PREFIX}tbia_records/select',
            data=json.dumps(query),
            headers={'content-type': 'application/json'},
        ).json()

        buckets = resp['facets']['stat_rightsHolder']['buckets']
        buckets.append({'val': 'total', 'count': resp['response']['numFound']})

        group_map = {**rights_holder_map, 'total': 'total'}

        DataStat.objects.filter(year_month=year_month, type='data').delete()
        DataStat.objects.bulk_create([
            DataStat(
                year_month=year_month,
                count=b['count'],
                rights_holder=b['val'],
                group=group_map[b['val']],
                type='data',
            )
            for b in buckets if b['val'] in group_map
        ])

        self.stdout.write(self.style.SUCCESS(f'{year_month} 統計完成'))