from pathlib import Path, PurePosixPath

import boto3
from botocore.config import Config
from django.conf import settings


SUPPORTED_SOURCE_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
MAX_SOURCE_SIZE = 50 * 1024 * 1024


class DiskUnavailable(RuntimeError):
    pass


def is_configured():
    return all((
        settings.DISK_S3_ENDPOINT,
        settings.DISK_S3_BUCKET,
        settings.DISK_S3_ACCESS_KEY,
        settings.DISK_S3_SECRET_KEY,
    ))


def client():
    if not is_configured():
        raise DiskUnavailable("DiskSL не настроен")
    return boto3.client(
        "s3",
        endpoint_url=settings.DISK_S3_ENDPOINT,
        region_name=settings.DISK_S3_REGION,
        aws_access_key_id=settings.DISK_S3_ACCESS_KEY,
        aws_secret_access_key=settings.DISK_S3_SECRET_KEY,
        config=Config(
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 3, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )


def _validate_source_key(key):
    prefix = settings.DISK_S3_KEY_PREFIX
    if not key.startswith(prefix) or "/оригиналы/" not in key:
        raise ValueError("Недопустимый путь DiskSL")
    if Path(key).suffix.lower() not in SUPPORTED_SOURCE_EXTENSIONS:
        raise ValueError("Неподдерживаемый формат документа")
    return key


def list_originals(client_sl_id=None):
    if not is_configured():
        return []
    storage = client()
    paginator = storage.get_paginator("list_objects_v2")
    items = []
    for page in paginator.paginate(Bucket=settings.DISK_S3_BUCKET, Prefix=settings.DISK_S3_KEY_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if obj.get("Size", 0) <= 0 or "/оригиналы/" not in key:
                continue
            if client_sl_id and f"({client_sl_id.upper()})/" not in key.upper():
                continue
            if Path(key).suffix.lower() not in SUPPORTED_SOURCE_EXTENSIONS:
                continue
            label = key.removeprefix(settings.DISK_S3_KEY_PREFIX)
            items.append({"key": key, "label": label, "size": obj["Size"]})
    return sorted(items, key=lambda item: item["label"].casefold())


def download_original(key):
    key = _validate_source_key(key)
    storage = client()
    metadata = storage.head_object(Bucket=settings.DISK_S3_BUCKET, Key=key)
    if metadata["ContentLength"] > MAX_SOURCE_SIZE:
        raise ValueError("Документ превышает 50 МБ")
    response = storage.get_object(Bucket=settings.DISK_S3_BUCKET, Key=key)
    return PurePosixPath(key).name, response["Body"].read()


def upload_translation(source_key, filename, content):
    source_key = _validate_source_key(source_key)
    student_root = source_key.split("/оригиналы/", 1)[0]
    safe_name = PurePosixPath(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("Недопустимое имя результата")
    destination = f"{student_root}/переводы/{safe_name}"
    client().put_object(
        Bucket=settings.DISK_S3_BUCKET,
        Key=destination,
        Body=content,
    )
    return destination
