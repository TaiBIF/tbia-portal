import json
import logging

import requests
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


class SolrTimeoutMiddleware:
    """Solr 請求逾時（requests.Timeout）時回 504：
    AJAX / POST / API → JSON，前端既有的 xhr.status == 504 會顯示「要求連線逾時」；
    一般頁面 → 沿用 500.html 版面，狀態碼 504。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, requests.exceptions.Timeout):
            return None
        logger.warning('Solr timeout: %s %s', request.method, request.get_full_path())
        is_ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest'
                   or request.method == 'POST' or request.path.startswith('/api/'))
        if is_ajax:
            return HttpResponse(json.dumps({'message': 'timeout'}), status=504,
                                content_type='application/json')
        return render(request, '500.html', status=504)
