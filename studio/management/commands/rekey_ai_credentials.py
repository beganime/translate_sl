import os

from cryptography.fernet import InvalidToken
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from studio.models import AIConfiguration, _fernet


class Command(BaseCommand):
    help = "Re-encrypt Gemini API credentials using environment-provided secrets."

    def handle(self, *args, **options):
        old_secret = os.getenv("OLD_DATA_ENCRYPTION_SECRET", "")
        new_secret = os.getenv("DATA_ENCRYPTION_SECRET", "")
        if not old_secret or not new_secret:
            raise CommandError("Set OLD_DATA_ENCRYPTION_SECRET and DATA_ENCRYPTION_SECRET in the environment.")
        if old_secret == new_secret:
            raise CommandError("Old and new encryption secrets must be different.")

        changed = 0
        with transaction.atomic():
            for config in AIConfiguration.objects.exclude(api_key_encrypted=""):
                try:
                    plain = _fernet(old_secret).decrypt(config.api_key_encrypted.encode())
                except InvalidToken as exc:
                    raise CommandError(f"Cannot decrypt AI configuration #{config.pk} with the old secret.") from exc
                config.api_key_encrypted = _fernet(new_secret).encrypt(plain).decode()
                config.save(update_fields=["api_key_encrypted", "updated_at"])
                changed += 1
        self.stdout.write(self.style.SUCCESS(f"Re-encrypted {changed} AI configuration(s)."))
