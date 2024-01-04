import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token


@require_POST
def register_view(request):
    return JsonResponse({"success": True})


@ensure_csrf_cookie
def get_csrf(request):
    response = JsonResponse({"details": "CSRF cookie set"})
    response["X-CSRFToken"] = get_token(request)
    return response
