from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from accounts.models import Membership


def _me_payload(user):
    membership = (
        Membership.objects.filter(user=user).select_related("workspace").first()
    )
    ws = membership.workspace if membership else None
    return {
        "id": user.id,
        "username": user.get_username(),
        "email": user.email,
        "workspace": {"id": ws.id, "name": ws.name} if ws else None,
    }


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return Response(
                {"detail": "invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        login(request, user)
        return Response(_me_payload(user))


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name="get")
class MeView(APIView):
    def get(self, request):
        return Response(_me_payload(request.user))
