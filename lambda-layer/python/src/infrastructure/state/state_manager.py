"""
StateManagementComponent (C9) — Gestión del JSON de fuente única de verdad.
Persiste en S3 (payload) + DynamoDB (índice de estado).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.schema.schema_validator import ValidationResult, is_valid_state_transition, validate_subject_json
from src.infrastructure.state.models import S3Reference, StateMetadata, SubjectState, SubjectSummary

logger = get_logger(__name__)

_RETRY_CONFIG = Config(retries={"max_attempts": 3, "mode": "adaptive"})


def _bucket_name() -> str:
    return os.environ["SUBJECTS_BUCKET_NAME"]


def _table_name() -> str:
    return os.environ["SUBJECTS_TABLE_NAME"]


def _s3_client():
    return boto3.client("s3", config=_RETRY_CONFIG)


def _dynamodb_resource():
    return boto3.resource("dynamodb", config=_RETRY_CONFIG)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_subject_json(subject_json: dict) -> S3Reference:
    """
    Valida y persiste el JSON de la asignatura en S3 (versionado).
    Lanza ValueError si el JSON no es válido (BR-09).
    """
    result: ValidationResult = validate_subject_json(subject_json)
    if not result.is_valid:
        raise ValueError(f"JSON inválido: {result.errors}")

    subject_id: str = subject_json["subject_id"]
    key = f"subjects/{subject_id}/subject.json"
    body = json.dumps(subject_json, ensure_ascii=False, indent=2).encode("utf-8")

    s3 = _s3_client()
    response = s3.put_object(
        Bucket=_bucket_name(),
        Key=key,
        Body=body,
        ContentType="application/json",
        ServerSideEncryption="aws:kms",
    )
    version_id = response.get("VersionId")
    logger.info("save_subject_json", extra={"subject_id": subject_id, "s3_key": key, "version_id": version_id})
    return S3Reference(bucket=_bucket_name(), key=key, version_id=version_id)


def update_subject_state(
    subject_id: str,
    new_state: SubjectState,
    metadata: StateMetadata,
) -> None:
    """
    Transiciona el estado de la asignatura.
    Valida la transición (BR-04), actualiza el JSON en S3 y el índice en DynamoDB (BR-10).
    Lanza ValueError si la transición no es válida.
    """
    subject_json = get_subject_json(subject_id)
    current_state: str = subject_json["pipeline_state"]["current_state"]

    if not is_valid_state_transition(current_state, new_state.value):
        raise ValueError(
            f"Transición inválida: {current_state} → {new_state.value}"
        )

    now = datetime.now(timezone.utc).isoformat()
    result_hash = hashlib.sha256(
        json.dumps(subject_json, sort_keys=True).encode()
    ).hexdigest()

    # Append-only state history (BR-03)
    subject_json["pipeline_state"]["state_history"].append({
        "state": new_state.value,
        "agent": metadata.agent,
        "timestamp": now,
        "llm_version": metadata.llm_version,
        "result_hash": metadata.result_hash or result_hash,
    })
    subject_json["pipeline_state"]["current_state"] = new_state.value
    subject_json["updated_at"] = now

    save_subject_json(subject_json)
    _upsert_state_record(subject_id, subject_json, new_state.value)

    logger.info(
        "update_subject_state",
        extra={"subject_id": subject_id, "from": current_state, "to": new_state.value},
    )


def get_subject_json(subject_id: str) -> dict:
    """Recupera el JSON más reciente de la asignatura desde S3."""
    key = f"subjects/{subject_id}/subject.json"
    s3 = _s3_client()
    try:
        response = s3.get_object(Bucket=_bucket_name(), Key=key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchKey":
            raise KeyError(f"Asignatura no encontrada: {subject_id}") from exc
        raise


def list_subjects_by_state(state: SubjectState) -> list[SubjectSummary]:
    """Lista asignaturas filtradas por estado usando GSI-1."""
    table = _dynamodb_resource().Table(_table_name())
    response = table.query(
        IndexName="state-index",
        KeyConditionExpression="current_state = :s",
        ExpressionAttributeValues={":s": state.value},
        ScanIndexForward=False,
    )
    return [
        SubjectSummary(
            subject_id=item["subject_id"],
            subject_name=item.get("subject_name", ""),
            program_name=item.get("program_name", ""),
            current_state=item["current_state"],
            updated_at=item["updated_at"],
            s3_key=item["s3_key"],
        )
        for item in response.get("Items", [])
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _upsert_state_record(subject_id: str, subject_json: dict, new_state: str) -> None:
    """Actualiza el índice de estado en DynamoDB (BR-10)."""
    table = _dynamodb_resource().Table(_table_name())
    table.put_item(
        Item={
            "subject_id": subject_id,
            "SK": "STATE",
            "current_state": new_state,
            "subject_name": subject_json["metadata"]["subject_name"],
            "program_name": subject_json["metadata"]["program_name"],
            "updated_at": subject_json["updated_at"],
            "s3_key": f"subjects/{subject_id}/subject.json",
        }
    )
