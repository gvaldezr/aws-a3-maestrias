"""
Persist agent results back to the Subject JSON in S3.
Called by Step Functions after each agent completes.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3

from src.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

BUCKET = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
TABLE = os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")


def _get_json(s3, subject_id: str) -> dict:
    obj = s3.get_object(Bucket=BUCKET, Key=f"subjects/{subject_id}/subject.json")
    return json.loads(obj["Body"].read().decode("utf-8"))


def _save_json(s3, subject_id: str, data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    s3.put_object(
        Bucket=BUCKET,
        Key=f"subjects/{subject_id}/subject.json",
        Body=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    # Update DynamoDB state index
    ddb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    table = ddb.Table(TABLE)
    table.put_item(Item={
        "subject_id": subject_id,
        "SK": "STATE",
        "current_state": data["pipeline_state"]["current_state"],
        "subject_name": data["metadata"]["subject_name"],
        "program_name": data["metadata"]["program_name"],
        "updated_at": data["updated_at"],
        "s3_key": f"subjects/{subject_id}/subject.json",
    })


def persist_scholar(event: dict, context: Any) -> dict:
    """Persist Scholar results into Subject JSON. Update state to KNOWLEDGE_MATRIX_READY."""
    subject_id = event.get("subject_id") or event.get("scholar", {}).get("subject_id", "")
    scholar_result = event.get("scholar", {}).get("result", {})
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))

    logger.info("persist_scholar", extra={"subject_id": subject_id})
    sj = _get_json(s3, subject_id)

    # Extract papers and matrix from agent response (may be in "result" key)
    result_text = scholar_result.get("result", "")
    try:
        parsed = json.loads(result_text) if isinstance(result_text, str) else result_text
    except (json.JSONDecodeError, TypeError):
        parsed = {}

    sj.setdefault("research", {})
    if parsed.get("top20_papers"):
        sj["research"]["top20_papers"] = parsed["top20_papers"]
    if parsed.get("knowledge_matrix"):
        sj["research"]["knowledge_matrix"] = parsed["knowledge_matrix"]
    if parsed.get("keywords_used"):
        sj["research"]["keywords"] = parsed["keywords_used"]

    sj["pipeline_state"]["current_state"] = "KNOWLEDGE_MATRIX_READY"
    now = datetime.now(timezone.utc).isoformat()
    sj["pipeline_state"]["state_history"].append({
        "state": "KNOWLEDGE_MATRIX_READY", "agent": "scholar-agent",
        "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": "",
    })

    _save_json(s3, subject_id, sj)
    logger.info("persist_scholar_done", extra={"subject_id": subject_id})
    return {"subject_id": subject_id, "state": "KNOWLEDGE_MATRIX_READY"}


def persist_di(event: dict, context: Any) -> dict:
    """Persist DI results into Subject JSON. Update state to DI_READY."""
    subject_id = event.get("subject_id") or event.get("di", {}).get("subject_id", "")
    di_result = event.get("di", {}).get("result", {})
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))

    logger.info("persist_di", extra={"subject_id": subject_id})
    sj = _get_json(s3, subject_id)

    result_text = di_result.get("result", "")
    try:
        parsed = json.loads(result_text) if isinstance(result_text, str) else result_text
    except (json.JSONDecodeError, TypeError):
        parsed = {}

    sj.setdefault("instructional_design", {})
    if parsed.get("objectives"):
        sj["instructional_design"]["learning_objectives"] = parsed["objectives"]
    if parsed.get("traceability_matrix"):
        sj["instructional_design"]["traceability_matrix"] = parsed["traceability_matrix"]
    if parsed.get("descriptive_card"):
        sj["instructional_design"]["descriptive_card"] = parsed["descriptive_card"]
    if parsed.get("content_map"):
        sj["instructional_design"]["content_map"] = parsed["content_map"]

    sj["pipeline_state"]["current_state"] = "DI_READY"
    now = datetime.now(timezone.utc).isoformat()
    sj["pipeline_state"]["state_history"].append({
        "state": "DI_READY", "agent": "di-agent",
        "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": "",
    })

    _save_json(s3, subject_id, sj)
    return {"subject_id": subject_id, "state": "DI_READY"}


def persist_content(event: dict, context: Any) -> dict:
    """Persist Content results into Subject JSON. Update state to CONTENT_READY."""
    subject_id = event.get("subject_id") or event.get("content", {}).get("subject_id", "")
    content_result = event.get("content", {}).get("result", {})
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))

    logger.info("persist_content", extra={"subject_id": subject_id})
    sj = _get_json(s3, subject_id)

    result_text = content_result.get("result", "")
    try:
        parsed = json.loads(result_text) if isinstance(result_text, str) else result_text
    except (json.JSONDecodeError, TypeError):
        parsed = {}

    sj.setdefault("content_package", {})
    if parsed.get("executive_readings"):
        sj["content_package"]["executive_readings"] = parsed["executive_readings"]
    if parsed.get("quizzes"):
        sj["content_package"]["quizzes"] = parsed["quizzes"]
    if parsed.get("maestria_artifacts"):
        sj["content_package"]["maestria_artifacts"] = parsed["maestria_artifacts"]
    if parsed.get("lab_cases"):
        sj["content_package"]["lab_cases"] = parsed["lab_cases"]

    sj["pipeline_state"]["current_state"] = "CONTENT_READY"
    now = datetime.now(timezone.utc).isoformat()
    sj["pipeline_state"]["state_history"].append({
        "state": "CONTENT_READY", "agent": "content-agent",
        "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": "",
    })

    _save_json(s3, subject_id, sj)
    return {"subject_id": subject_id, "state": "CONTENT_READY"}
