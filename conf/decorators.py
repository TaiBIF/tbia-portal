from django.contrib.auth.decorators import user_passes_test


def check_user(user):
    return not user.is_authenticated


user_logout_required = user_passes_test(check_user, '/', None)


def auth_user_should_not_access(viewfunc):
    return user_logout_required(viewfunc)

def system_admin_post_required(viewfunc):
    """限系統管理員 + POST（搭配 CsrfViewMiddleware 即有 CSRF 保護）"""
    from functools import wraps
    from django.http import JsonResponse

    @wraps(viewfunc)
    def _wrapped(request, *args, **kwargs):
        if request.method != 'POST':
            return JsonResponse({'status': 'fail', 'message': 'Method not allowed'}, status=405)
        if not request.user.is_authenticated or not getattr(request.user, 'is_system_admin', False):
            return JsonResponse({'status': 'fail', 'message': 'Permission denied'}, status=403)
        return viewfunc(request, *args, **kwargs)
    return _wrapped
