from asyncio import iscoroutinefunction
from functools import wraps

from django.http import JsonResponse


def user_passes_test(test_func):
    def decorator(view_func):
        if iscoroutinefunction(view_func):

            @wraps(view_func)
            async def _wrapped_view(request, *args, **kwargs):
                if test_func(request.user):
                    return await view_func(request, *args, **kwargs)
                return JsonResponse({"details": "Unauthorized"}, status=401)
        else:

            @wraps(view_func)
            def _wrapped_view(request, *args, **kwargs):
                if test_func(request.user):
                    return view_func(request, *args, **kwargs)
                return JsonResponse({"details": "Unauthorized"}, status=401)

        return _wrapped_view

    return decorator


def login_required_401(function=None):
    actual_decorator = user_passes_test(
        lambda u: not u.is_anonymous,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
