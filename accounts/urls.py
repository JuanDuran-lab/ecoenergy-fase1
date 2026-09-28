from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.EcoLoginView.as_view(), name="login"),
    path("logout/", views.EcoLogoutView.as_view(), name="logout"),
    path("recuperar/", views.password_reset_request, name="password_reset_request"),
    path("recuperar/confirmar/", views.password_reset_confirm, name="password_reset_confirm"),
]
