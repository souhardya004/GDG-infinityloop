from django.urls import path

from apps.authentication.views import (
    DemoLoginView,
    GitHubAuthView,
    GoogleAuthView,
    LoginView,
    LogoutView,
    MeView,
    ProvidersConfigView,
    SignupView,
)

urlpatterns = [
    path("me/", MeView.as_view(), name="auth-me"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("signup/", SignupView.as_view(), name="auth-signup"),
    path("github/", GitHubAuthView.as_view(), name="auth-github"),
    path("google/", GoogleAuthView.as_view(), name="auth-google"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("demo/", DemoLoginView.as_view(), name="auth-demo"),
    path("providers/", ProvidersConfigView.as_view(), name="auth-providers"),
]
