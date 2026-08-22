import hashlib
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET


SSO_SALT = "manager-sl.translate-sso.v1"


def _safe_local_path(value):
    value = str(value or "").strip()
    parsed = urlsplit(value)
    if (
        not value.startswith("/")
        or value.startswith("//")
        or "\\" in value
        or parsed.scheme
        or parsed.netloc
    ):
        return reverse("studio:dashboard")
    return value


@require_GET
def manager_sl_sso(request):
    """Accept a short-lived ManagerSL identity without sharing passwords."""

    secret = settings.MANAGER_SL_SSO_SECRET
    if not secret:
        return HttpResponse("Связь с ManagerSL не настроена.", status=503)

    token = request.GET.get("token", "")
    try:
        payload = signing.loads(
            token,
            key=secret,
            salt=SSO_SALT,
            max_age=settings.MANAGER_SL_SSO_MAX_AGE,
        )
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return HttpResponse("Ссылка входа недействительна или устарела.", status=400)

    email = str(payload.get("email") or "").strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return HttpResponse("ManagerSL передал некорректного пользователя.", status=400)

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).order_by("id").first()
    if user is None:
        username = f"manager-{hashlib.sha256(email.encode('utf-8')).hexdigest()[:32]}"
        user = User(username=username, email=email)
        user.set_unusable_password()

    update_fields = []
    for field in ("first_name", "last_name"):
        value = str(payload.get(field) or "").strip()[:150]
        if getattr(user, field) != value:
            setattr(user, field, value)
            update_fields.append(field)

    if not user.is_active:
        user.is_active = True
        update_fields.append("is_active")
    desired_staff = bool(payload.get("is_staff"))
    if not user.is_superuser and user.is_staff != desired_staff:
        user.is_staff = desired_staff
        update_fields.append("is_staff")

    if user.pk:
        if update_fields:
            user.save(update_fields=update_fields)
    else:
        user.save()

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(12 * 60 * 60)
    response = redirect(_safe_local_path(payload.get("next")))
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response
