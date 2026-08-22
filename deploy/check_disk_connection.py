"""Read-only production check for the TranslateSL -> DiskSL connection."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.getenv("TRANSLATESL_ROOT", str(Path(__file__).resolve().parents[1])))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "translate_sl.settings")

import django

django.setup()

from studio.services.disk import is_configured, list_originals


if not is_configured():
    raise SystemExit("DiskSL is not configured")

originals = list_originals()
print(f"DiskSL connection OK; originals available: {len(originals)}")
