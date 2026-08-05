import os
import re
import secrets
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "translate_sl.settings")
sys.path.insert(0, "/app")

import django

django.setup()

import requests
from django.contrib.auth import get_user_model


base_url = "https://translate.manager-sl.ru"
login_url = f"{base_url}/accounts/login/"
username = f"codex-login-probe-{secrets.token_hex(5)}"
password = secrets.token_urlsafe(32)
user = get_user_model().objects.create_user(username=username, password=password)

try:
    session = requests.Session()
    login_page = session.get(login_url, timeout=30)
    login_page.raise_for_status()
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
    if not match:
        raise RuntimeError("CSRF token was not found on the login page.")
    response = session.post(
        login_url,
        data={
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": match.group(1),
            "next": "/",
        },
        headers={"Referer": login_url},
        allow_redirects=False,
        timeout=30,
    )
    dashboard = session.get(f"{base_url}/", allow_redirects=False, timeout=30)
    if response.status_code != 302 or dashboard.status_code != 200:
        raise RuntimeError(
            f"Login probe failed: login={response.status_code}, dashboard={dashboard.status_code}, location={response.headers.get('Location')}"
        )
    print("production_login_ok login=302 dashboard=200")
finally:
    user.delete()
    print("temporary_test_user_deleted")
