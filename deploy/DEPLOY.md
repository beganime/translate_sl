# Развёртывание TranslateSL на Ubuntu

Инструкция рассчитана на Ubuntu 24.04, домен `translate.manager-sl.ru` и сохранение текущих `db.sqlite3` и `media/`.

## 1. DNS в REG.RU

В зоне домена `manager-sl.ru` создайте запись:

- тип: `A`;
- поддомен/имя: `translate`;
- значение: публичный IPv4 вашего сервера.

Если сервер имеет IPv6, дополнительно можно создать `AAAA`. Не создавайте одновременно `CNAME` и `A` для одного имени. Перед выпуском сертификата проверьте с компьютера: `nslookup translate.manager-sl.ru` должен вернуть IP сервера.

## 2. Подготовка сервера

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx sqlite3 libreoffice-writer certbot python3-certbot-nginx unzip
sudo adduser --system --home /opt/translate-sl --group translate
sudo usermod -a -G www-data translate
sudo mkdir -p /opt/translate-sl /var/backups/translate-sl
sudo chown -R translate:www-data /opt/translate-sl /var/backups/translate-sl
```

Откройте во внешнем firewall порты TCP `80` и `443`. SSH (`22`) лучше разрешить только с доверенных IP.

## 3. Передача проекта вместе с текущей базой

На Windows выполните:

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\build_bundle.ps1
scp .\TranslateSL-deploy.zip root@SERVER_IP:/tmp/
```

На сервере:

```bash
sudo -u translate unzip /tmp/TranslateSL-deploy.zip -d /opt/translate-sl
sudo -u translate python3 -m venv /opt/translate-sl/.venv
sudo -u translate /opt/translate-sl/.venv/bin/pip install --upgrade pip
sudo -u translate /opt/translate-sl/.venv/bin/pip install -r /opt/translate-sl/requirements.txt
sudo chown -R translate:www-data /opt/translate-sl
sudo find /opt/translate-sl/media -type d -exec chmod 750 {} \;
sudo find /opt/translate-sl/media -type f -exec chmod 640 {} \;
sudo chmod 750 /opt/translate-sl/deploy/backup.sh
```

Архив содержит персональные документы, поэтому после распаковки удалите `/tmp/TranslateSL-deploy.zip` и не отправляйте архив через публичные файлообменники.

## 4. Секреты и перенос зашифрованного API-ключа

Создайте два разных секрета:

```bash
openssl rand -base64 48
openssl rand -base64 48
sudo nano /etc/translate-sl.env
sudo chmod 640 /etc/translate-sl.env
sudo chown root:www-data /etc/translate-sl.env
```

Содержимое берётся из `.env.production.example`. Первый результат вставьте в `DJANGO_SECRET_KEY`, второй — в `DATA_ENCRYPTION_SECRET`.

В текущей базе Gemini-ключ зашифрован старым development-секретом. Временно добавьте в `/etc/translate-sl.env` строку `OLD_DATA_ENCRYPTION_SECRET=dev-only-change-me-translate-sl`, один раз перенесите ключ и сразу удалите эту строку:

```bash
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; exec /opt/translate-sl/.venv/bin/python /opt/translate-sl/manage.py rekey_ai_credentials'
sudo nano /etc/translate-sl.env  # удалить OLD_DATA_ENCRYPTION_SECRET
```

Альтернатива ротации — после запуска заново ввести Gemini API-ключ через админку.

## 5. Django и сервис

```bash
cd /opt/translate-sl
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; cd /opt/translate-sl; .venv/bin/python manage.py migrate'
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; cd /opt/translate-sl; .venv/bin/python manage.py collectstatic --noinput'
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; cd /opt/translate-sl; .venv/bin/python manage.py check --deploy'

sudo cp deploy/translate-sl.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now translate-sl
sudo systemctl status translate-sl
```

Для создания первого администратора:

```bash
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; exec /opt/translate-sl/.venv/bin/python /opt/translate-sl/manage.py createsuperuser'
```

Обычных менеджеров создавайте в `/admin/auth/user/`: включайте `Активный`, но не давайте `Статус персонала` и права суперпользователя. Они смогут работать с документами, но не менять API-ключ и шаблоны.

## 6. Nginx и HTTPS

```bash
sudo cp /opt/translate-sl/deploy/nginx-translate.manager-sl.ru.conf /etc/nginx/sites-available/translate.manager-sl.ru
sudo ln -s /etc/nginx/sites-available/translate.manager-sl.ru /etc/nginx/sites-enabled/translate.manager-sl.ru
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d translate.manager-sl.ru
```

После выпуска сертификата проверьте `https://translate.manager-sl.ru`, вход менеджера, загрузку многостраничного PDF, предпросмотр и скачивание DOCX/PDF.

## 7. Ежедневные резервные копии

```bash
sudo cp /opt/translate-sl/deploy/translate-sl-backup.service /etc/systemd/system/
sudo cp /opt/translate-sl/deploy/translate-sl-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now translate-sl-backup.timer
sudo systemctl start translate-sl-backup.service
ls -lh /var/backups/translate-sl
```

Копии хранятся 14 дней. Дополнительно копируйте их на другой сервер или закрытое облачное хранилище: диск самого сервера не является полноценной резервной копией.

## Обновление

Перед заменой файлов запустите backup, загрузите новый код без перезаписи `db.sqlite3`, `media/` и `/etc/translate-sl.env`, затем:

```bash
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; cd /opt/translate-sl; .venv/bin/python manage.py migrate'
sudo -u translate bash -c 'set -a; source /etc/translate-sl.env; set +a; cd /opt/translate-sl; .venv/bin/python manage.py collectstatic --noinput'
sudo systemctl restart translate-sl
```
