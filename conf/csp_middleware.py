from csp.middleware import CSPMiddleware


class DynamicCSPMiddleware(CSPMiddleware):
    """
    同時支援：
      1. django-csp 4.0 內建的 @csp_update / @csp_replace 裝飾器（父類別處理）
      2. View 端動態設定 response._csp_dynamic_update（本類別處理）
    """

    def get_policy_parts(self, request, response, report_only=False):
        policy_parts = super().get_policy_parts(request, response, report_only)

        if report_only:
            return policy_parts

        update = getattr(response, '_csp_dynamic_update', None)
        if update:
            if policy_parts.update is None:
                policy_parts.update = {}
            for directive, sources in update.items():
                existing = list(policy_parts.update.get(directive, []))
                policy_parts.update[directive] = existing + list(sources)

        return policy_parts