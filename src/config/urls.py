from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.api import LoginView, LogoutView, MeView
from digests.api import DigestViewSet
from matching.api import MatchViewSet
from watches.api import ClientViewSet, WatchViewSet

router = DefaultRouter(trailing_slash=False)
router.register("clients", ClientViewSet, basename="client")
router.register("watches", WatchViewSet, basename="watch")
router.register("matches", MatchViewSet, basename="match")
router.register("digests", DigestViewSet, basename="digest")

urlpatterns = [
    path("api/auth/login", LoginView.as_view(), name="login"),
    path("api/auth/logout", LogoutView.as_view(), name="logout"),
    path("api/me", MeView.as_view(), name="me"),
    path("api/", include(router.urls)),
]
