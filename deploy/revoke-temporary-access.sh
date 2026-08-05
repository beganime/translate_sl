#!/usr/bin/env bash
set -euo pipefail

bad_media="/opt/translate-sl/data/media-archive-bad"
if [[ -e "$bad_media" ]]; then
  resolved="$(readlink -f "$bad_media")"
  [[ "$resolved" == "$bad_media" ]]
  ! mountpoint -q "$bad_media"
  rm -rf -- "$bad_media"
fi

# An earlier unused build layer contained the malformed media copy. Removing
# unused build cache does not affect running containers or tagged images.
docker builder prune -f >/dev/null

rm -f \
  /tmp/audit_media.py \
  /tmp/views.py \
  /tmp/dashboard.html \
  /tmp/dockerignore \
  /tmp/test_production_login.py \
  /tmp/run-login-check.sh \
  /tmp/revoke-temporary-access.sh

rm -f /etc/sudoers.d/translatesl-deploy
rm -rf /home/translatesl-deploy/.ssh
usermod -L translatesl-deploy

echo "temporary_access_revoked"
