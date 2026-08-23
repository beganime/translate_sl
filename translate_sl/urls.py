from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path

from .views import manager_sl_sso

admin.site.site_header = "TranslateSL — управление"
admin.site.site_title = "TranslateSL"
admin.site.index_title = "Шаблоны и настройки"


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ok", "storage": "local"})

urlpatterns = [
    path("health/", health, name="health"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/manager-sl/", manager_sl_sso, name="manager_sl_sso"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("", include("studio.urls")),
]
