from django.conf import settings


def service_links(_request):
    return {
        "manager_sl_url": settings.MANAGER_SL_URL,
        "manager_sl_translate_url": settings.MANAGER_SL_TRANSLATE_URL,
        "disk_sl_url": settings.DISK_SL_URL,
    }
