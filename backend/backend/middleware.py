from account.models import UserToken
from django.contrib.auth.models import User
from django.core.cache import cache


class DisableCSRFMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, "_dont_enforce_csrf_checks", True)
        return self.get_response(request)


class JWTAuthenticaitonMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get("authorization", None)
        if not token:
            return self.get_response(request)
        token = token[7:]
        user_token = UserToken.objects.filter(access_token=token).first()
        if not user_token:
            return self.get_response(request)
        if not user_token.is_token_valid():
            return self.get_response(request)
        setattr(request, "user", user_token.user)
        cache.set(user_token.user.id, "online", timeout=60 * 5)
        return self.get_response(request)
