from django.urls import path

from accounts.api import LoginView, LogoutView, MeView

urlpatterns = [
    path("api/auth/login", LoginView.as_view(), name="login"),
    path("api/auth/logout", LogoutView.as_view(), name="logout"),
    path("api/me", MeView.as_view(), name="me"),
]
