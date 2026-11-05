""" python manage.py run_worker

worker 容器的啟動指令：先把上次 worker 中斷時仍被鎖住（未完成）的背景工作解鎖，再啟動 qcluster。
未完成的工作原本要等 Q_CLUSTER['retry'] 秒（約一天）才會重新派送，解鎖後重啟就會立即補跑。

注意：只適用於「只有一個 worker 容器」的部署；若同時有多個 qcluster，會把其他 worker 正在跑的工作也解鎖。
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import OrmQ


class Command(BaseCommand):
    help = '解鎖上次中斷的背景工作後啟動 qcluster'

    def handle(self, *args, **options):
        n = OrmQ.objects.filter(lock__gt=timezone.now()).update(lock=timezone.now())
        self.stdout.write(f'unlocked {n} interrupted task(s)')
        call_command('qcluster')
