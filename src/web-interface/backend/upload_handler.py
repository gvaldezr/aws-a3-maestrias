"""
Upload Handler — U7: Genera presigned URL para carga directa a S3.
Lambda invocado por API Gateway: POST /api/upload
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.observability.metrics import record_metric
from src.web_interface.backend.document_parser import validate_upload

logger = get_logger(__name__)

_SECURITY_HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
}


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Genera presigned URL de S3 para carga directa del documento.
    El Staff carga el archivo directamente a S3 desde el browser.
    """
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    file_name: str = body.get("file_name", "")
    file_size: int = body.get("file_size_bytes", 0)
    content_type: str = body.get("content_type", "")

    if not file_name:
        return _response(400, {"error": "file_name is required"})

    # Validar formato y tamaño (BR-W01, BR-W02)
    validation = validate_upload(file_name, file_size, content_type)
    if not validation.is_valid:
        return _response(400, {"errors": validation.errors})

    subject_id = str(uuid.uuid4())
    s3_key = f"uploads/{subject_id}/{file_name}"
    bucket = os.environ["SUBJECTS_BUCKET_NAME"]

    s3_client = boto3.client("s3")
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": s3_key, "ContentType": content_type},
        ExpiresIn=300,  # 5 minutos
    )

    record_metric("DocumentsUploaded", 1, "Count")
    logger.info("upload_presigned_url_generated", extra={"subject_id": subject_id, "file_name": file_name})

    return _response(200, {
        "subject_id": subject_id,
        "upload_url": presigned_url,
        "s3_key": s3_key,
        "expires_in_seconds": 300,
    })


def _response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "headers": _SECURITY_HEADERS, "body": json.dumps(body)}
